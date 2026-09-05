from __future__ import annotations

import json
import re
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.schemas import ChatResponse, EvidenceTable, ToolTraceItem
from app.services.guide import list_schema_summary, load_database_guide
from app.services.sessions import ChatSession, session_store
from app.services.sql_guard import SqlValidationError, execute_readonly_sql


OPTIMIZE_FOR_VALUES = frozenset({"cost", "balanced", "intelligence"})

# Lightweight Gemini models (hackathon-friendly)
OPTIMIZE_FOR_MODELS = {
    "cost": "gemini-3.5-flash-lite",
    "balanced": "gemini-3.5-flash",
    "intelligence": "gemini-3.5-flash",
}

SYSTEM_INSTRUCTION = """
You are a finance assistant for a hackathon PostgreSQL database with exactly three tables:
bank, account, and "transaction" (always quote "transaction" in SQL).

SCHEMA (exact column names — do not invent columns like amount):
- bank(bank_code, bank_name)
- account(account_id, entity_id, account_number, program_id, available_balance, bank_code)
- "transaction"(transaction_id, account_id, transaction_date, transaction_type, description,
  transaction_amount, transaction_reference_id, utr_number)
- transaction_type is only 'credit' or 'debit' (use = 'debit', not ILIKE)

IMPORTANT RULES:
1. Never invent financial numbers, banks, accounts, or transactions.
2. When a question needs data, use tools. Tool results are the source of truth.
3. Use run_sql_query for facts. Prefer 1–2 targeted queries. Do NOT keep querying after you have the answer.
4. As soon as tool results answer the user, STOP calling tools and write the final plain-language answer.
5. Put filters/aggregates in SQL — do not calculate totals yourself from memory.
6. Mask account_number (last 4 only). Do not dump full utr_number.
7. Bare "reference" / "ref no" → transaction_reference_id. "UTR" → utr_number.
8. "Vendor" questions: there is no vendor table — search description; if no vendor keywords match,
   report total debits for the period and say vendor-specific labels were not found.
9. "Unreconciled": schema has no reconciliation column — say data is not available.
10. If ambiguous, ask one clarifying question instead of guessing.
11. For growth / trend / increasing / decreasing / spend over time questions, return a time-series
    SQL result with a date/month column and a numeric amount column (e.g. date_trunc('month', ...)
    and sum(transaction_amount)) so the UI can chart it.

Final reply format: short grounded answer. Optionally end with:
STATUS: answered | needs_clarification | insufficient_data
CONFIDENCE: high | medium | low
"""


TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="read_database_guide",
        description=(
            "Read the finance dataset / SQL guide (schema, joins, sensitive fields, "
            "query patterns). Call before writing SQL if unsure."
        ),
        parameters_json_schema={"type": "object", "properties": {}},
    ),
    types.FunctionDeclaration(
        name="list_tables",
        description=(
            "List columns for bank, account, and transaction from information_schema."
        ),
        parameters_json_schema={"type": "object", "properties": {}},
    ),
    types.FunctionDeclaration(
        name="run_sql_query",
        description=(
            "Run a single read-only PostgreSQL SELECT/WITH query against the finance DB. "
            'Quote the transaction table as "transaction".'
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A single SELECT or WITH statement",
                }
            },
            "required": ["sql"],
        },
    ),
]


def _resolve_optimize_for(optimize_for: str | None) -> str:
    mode = (
        optimize_for or settings.gemini_optimize_for or "balanced"
    ).strip().lower()
    if mode not in OPTIMIZE_FOR_VALUES:
        raise ValueError(
            f'Invalid optimize_for "{mode}". '
            f"Use one of: {', '.join(sorted(OPTIMIZE_FOR_VALUES))}"
        )
    return mode


def _resolve_model(optimize_for: str | None) -> tuple[str, str]:
    mode = _resolve_optimize_for(optimize_for)
    explicit = (settings.gemini_model or "").strip()
    if explicit:
        return explicit, mode
    return OPTIMIZE_FOR_MODELS[mode], mode


def _gemini_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to backend/.env "
            "(https://aistudio.google.com/apikey)."
        )
    return genai.Client(api_key=settings.gemini_api_key)


def _parse_status_confidence(answer: str) -> tuple[str, str, str]:
    status = "answered"
    confidence = "medium"
    cleaned = answer

    status_match = re.search(
        r"STATUS:\s*(answered|needs_clarification|insufficient_data)",
        answer,
        re.IGNORECASE,
    )
    if status_match:
        status = status_match.group(1).lower()
    conf_match = re.search(r"CONFIDENCE:\s*(high|medium|low)", answer, re.IGNORECASE)
    if conf_match:
        confidence = conf_match.group(1).lower()

    cleaned = re.sub(
        r"\n?STATUS:\s*(answered|needs_clarification|insufficient_data)\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"\n?CONFIDENCE:\s*(high|medium|low)\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    return cleaned, status, confidence


def _infer_status(
    answer: str,
    evidence: dict[str, Any],
    tool_trace: list[ToolTraceItem],
) -> tuple[str, str, str]:
    cleaned, status, confidence = _parse_status_confidence(answer)
    lower = cleaned.lower()
    sql_traces = [t for t in tool_trace if t.tool == "run_sql_query" and t.ok]
    if status == "answered" and sql_traces and all((t.row_count or 0) == 0 for t in sql_traces):
        status = "insufficient_data"
        confidence = "low"
    if "clarif" in lower or "which account" in lower:
        status = "needs_clarification"
    if "not in the schema" in lower or "no matching" in lower or "no reconciliation" in lower:
        if status == "answered":
            status = "insufficient_data"
    if "tool-call limit" in lower:
        confidence = "medium"
    if evidence.get("rows") and status == "answered" and confidence == "medium":
        if "tool-call limit" not in lower:
            confidence = "high"
    return cleaned, status, confidence


def _dispatch_tool(
    name: str,
    arguments: dict[str, Any],
    *,
    evidence_holder: dict[str, Any],
    tool_trace: list[ToolTraceItem],
) -> Any:
    try:
        if name == "read_database_guide":
            content = load_database_guide()
            tool_trace.append(
                ToolTraceItem(
                    tool=name, ok=True, detail=f"{len(content)} chars"
                )
            )
            return content

        if name == "list_tables":
            db = SessionLocal()
            try:
                content = list_schema_summary(db)
                tool_trace.append(ToolTraceItem(tool=name, ok=True))
                return content
            finally:
                db.close()

        if name == "run_sql_query":
            sql = str(arguments.get("sql") or "")
            db = SessionLocal()
            try:
                columns, rows, executed = execute_readonly_sql(db, sql)
                evidence_holder["columns"] = columns
                evidence_holder["rows"] = rows
                evidence_holder["sql"] = executed
                tool_trace.append(
                    ToolTraceItem(
                        tool=name, ok=True, sql=executed, row_count=len(rows)
                    )
                )
                return {
                    "columns": columns,
                    "rows": rows[:50],
                    "row_count": len(rows),
                    "sql": executed,
                }
            finally:
                db.close()

        tool_trace.append(ToolTraceItem(tool=name, ok=False, detail="Unknown tool"))
        return {"error": f"Unknown tool: {name}"}
    except SqlValidationError as exc:
        tool_trace.append(ToolTraceItem(tool=name, ok=False, detail=str(exc)))
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        tool_trace.append(ToolTraceItem(tool=name, ok=False, detail=str(exc)))
        return {"error": str(exc)}


def _extract_text(response: types.GenerateContentResponse) -> str:
    try:
        text = response.text
        if text:
            return text.strip()
    except Exception:
        pass
    parts: list[str] = []
    for candidate in response.candidates or []:
        content = candidate.content
        if not content or not content.parts:
            continue
        for part in content.parts:
            if part.text:
                parts.append(part.text)
    return "\n".join(parts).strip()


def _synthesize_final_answer(
    client: genai.Client,
    *,
    model: str,
    contents: list[types.Content],
    user_message: str,
    evidence_holder: dict[str, Any],
) -> str:
    """Force a text answer after tool rounds are exhausted."""
    evidence_summary = {
        "columns": evidence_holder.get("columns") or [],
        "rows": (evidence_holder.get("rows") or [])[:20],
        "sql": evidence_holder.get("sql"),
    }
    contents = list(contents)
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=(
                        "Stop calling tools. Using ONLY the tool results above "
                        f"(latest evidence JSON: {json.dumps(evidence_summary, default=str)}), "
                        f"answer this question now in plain language:\n{user_message}\n\n"
                        "If vendor-specific rows were empty, say so and report the debit totals you do have."
                    )
                )
            ],
        )
    )
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION.strip(),
            temperature=0.1,
        ),
    )
    return _extract_text(response) or (
        "Based on the query results available, I could not form a complete answer."
    )


def _run_gemini_tool_loop(
    *,
    model: str,
    history_messages: list[dict[str, str]],
    user_message: str,
    evidence_holder: dict[str, Any],
    tool_trace: list[ToolTraceItem],
) -> str:
    client = _gemini_client()
    contents: list[types.Content] = []
    for msg in history_messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=user_message)])
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION.strip(),
        temperature=0.1,
        tools=[types.Tool(function_declarations=TOOL_DECLARATIONS)],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    for _ in range(settings.max_tool_rounds):
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        function_calls = list(response.function_calls or [])
        if not function_calls:
            return _extract_text(response) or (
                "I could not produce an answer from the available data."
            )

        model_content = response.candidates[0].content if response.candidates else None
        if model_content is not None:
            contents.append(model_content)

        tool_parts: list[types.Part] = []
        for call in function_calls:
            name = call.name or ""
            args = dict(call.args or {})
            result = _dispatch_tool(
                name,
                args,
                evidence_holder=evidence_holder,
                tool_trace=tool_trace,
            )
            # Keep guide responses short in the transcript so the model stays focused
            if name == "read_database_guide" and isinstance(result, str) and len(result) > 2500:
                result = result[:2500] + "\n…[truncated]…"
            tool_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result}
                    if not isinstance(result, dict)
                    else result,
                )
            )
        contents.append(types.Content(role="user", parts=tool_parts))

        # If we already have successful SQL evidence, nudge toward answering next round
        # by allowing one more tool round only if needed; synthesis happens after loop.

    return _synthesize_final_answer(
        client,
        model=model,
        contents=contents,
        user_message=user_message,
        evidence_holder=evidence_holder,
    )


async def run_chat_agent(
    db: Session,
    session: ChatSession,
    user_message: str,
    *,
    optimize_for: str | None = None,
    retry: bool = False,
    previous_sql: str | None = None,
    previous_answer: str | None = None,
) -> ChatResponse:
    _ = db
    model, mode = _resolve_model(optimize_for)
    tool_trace: list[ToolTraceItem] = []
    evidence_holder: dict[str, Any] = {"columns": [], "rows": [], "sql": None}

    history_messages = [
        {"role": m["role"], "content": str(m.get("content") or "")}
        for m in session.messages[-8:]
        if m.get("role") in {"user", "assistant"} and m.get("content")
    ]

    prompt_message = user_message
    if retry:
        prompt_message = (
            f"The user gave thumbs-down on the previous answer and wants a better grounded result.\n"
            f"Original question: {user_message}\n"
            f"Previous SQL (DO NOT reuse this exact query): {previous_sql or 'unknown'}\n"
            f"Previous answer summary: {(previous_answer or '')[:500]}\n\n"
            "Write a DIFFERENT SQL approach (different filters, grouping, or date window), "
            "run it with run_sql_query, then answer from the new results only."
        )

    import asyncio

    raw_answer = await asyncio.to_thread(
        _run_gemini_tool_loop,
        model=model,
        history_messages=history_messages,
        user_message=prompt_message,
        evidence_holder=evidence_holder,
        tool_trace=tool_trace,
    )

    answer, status, confidence = _infer_status(raw_answer, evidence_holder, tool_trace)
    evidence = EvidenceTable(
        columns=list(evidence_holder.get("columns") or []),
        rows=list(evidence_holder.get("rows") or []),
        sql=evidence_holder.get("sql"),
    )

    # On retry, store as a new assistant turn for the same question context
    store_user = user_message if not retry else f"[retry] {user_message}"
    session_store.append_messages(
        session.session_id,
        [
            {"role": "user", "content": store_user},
            {"role": "assistant", "content": answer},
        ],
    )
    session_store.set_evidence(
        session.session_id,
        {"columns": evidence.columns, "rows": evidence.rows, "sql": evidence.sql},
    )

    return ChatResponse(
        session_id=session.session_id,
        answer=answer,
        message=answer,
        type="text",
        data=None,
        evidence=evidence,
        tool_trace=tool_trace,
        confidence=confidence,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        optimize_for=mode,  # type: ignore[arg-type]
        retried=retry,
    )
