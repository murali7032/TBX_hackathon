from __future__ import annotations

import json
import re
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.schemas import (
    ChatResponse,
    ClarificationChoice,
    EvidenceTable,
    InsightCallout,
    ToolTraceItem,
)
from app.services.finance_analytics import (
    analyze_debit_trends,
    find_accounts,
    matches_to_choices,
)
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
3. Prefer dedicated tools when they fit:
   - find_accounts: when user gives last-4 digits / partial account / bank+account ambiguity
   - analyze_debit_trends: for spend growth, MoM change, increasing/decreasing, anomalies
   - run_sql_query: for other targeted SELECT/WITH queries
4. Prefer 1–2 tool calls. STOP and answer as soon as you have enough data.
5. Ambiguity: if find_accounts returns match_count > 1, DO NOT pick an account.
   Tell the user to choose one option and end with STATUS: needs_clarification.
6. Mask account_number (last 4 only). Do not dump full utr_number.
7. Bare "reference" / "ref no" → transaction_reference_id. "UTR" → utr_number.
8. "Vendor" questions: no vendor table — search description; if empty, say so.
9. "Unreconciled": no reconciliation column — say data is not available.
10. For growth/spend questions, prefer analyze_debit_trends (includes MoM % and anomaly flags).

Final reply format: short grounded answer. Mention MoM % and anomalies when present.
Optionally end with:
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
        name="find_accounts",
        description=(
            "Find matching accounts by last 4 digits, bank_code, and/or partial account_number. "
            "Use when the user is ambiguous about which account. If multiple matches, do not guess."
        ),
        parameters_json_schema={
            "type": "object",
            "properties": {
                "last4": {
                    "type": "string",
                    "description": "Last 4 digits of account_number",
                },
                "bank_code": {
                    "type": "string",
                    "description": "Bank code e.g. HDFC, SBIN",
                },
                "account_number": {
                    "type": "string",
                    "description": "Partial or full account number",
                },
            },
        },
    ),
    types.FunctionDeclaration(
        name="analyze_debit_trends",
        description=(
            "Compute monthly debit totals with MoM % change (SQL LAG) and anomaly flags "
            "(month or txn > 2× median debit). Use for growth/spend/increasing/decreasing questions."
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
    *,
    choices: list[dict[str, str]] | None = None,
) -> tuple[str, str, str]:
    cleaned, status, confidence = _parse_status_confidence(answer)
    lower = cleaned.lower()
    sql_traces = [
        t
        for t in tool_trace
        if t.tool in {"run_sql_query", "analyze_debit_trends"} and t.ok
    ]
    if status == "answered" and sql_traces and all((t.row_count or 0) == 0 for t in sql_traces):
        status = "insufficient_data"
        confidence = "low"
    if choices and len(choices) > 1:
        status = "needs_clarification"
        confidence = "medium"
    if "clarif" in lower or "which account" in lower or "choose one" in lower:
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
    choices_holder: list[dict[str, str]],
    insights_holder: list[dict[str, str]],
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

        if name == "find_accounts":
            db = SessionLocal()
            try:
                result = find_accounts(
                    db,
                    last4=arguments.get("last4"),
                    bank_code=arguments.get("bank_code"),
                    account_number=arguments.get("account_number"),
                )
                matches = result.get("matches") or []
                if len(matches) > 1:
                    choices_holder.clear()
                    choices_holder.extend(matches_to_choices(matches))
                tool_trace.append(
                    ToolTraceItem(
                        tool=name, ok=True, row_count=len(matches), detail=result.get("hint")
                    )
                )
                return result
            finally:
                db.close()

        if name == "analyze_debit_trends":
            db = SessionLocal()
            try:
                result = analyze_debit_trends(db)
                evidence_holder["columns"] = result["columns"]
                evidence_holder["rows"] = result["rows"]
                evidence_holder["sql"] = result["sql"]
                insights_holder.clear()
                for item in result.get("anomalies") or []:
                    insights_holder.append(
                        {"type": item.get("type", "anomaly"), "message": item["message"]}
                    )
                # Also keep a few MoM narrative lines as insights
                for line in (result.get("insights") or [])[:6]:
                    if not any(i["message"] == line for i in insights_holder):
                        insights_holder.append({"type": "mom", "message": line})
                tool_trace.append(
                    ToolTraceItem(
                        tool=name,
                        ok=True,
                        sql=result["sql"],
                        row_count=len(result["rows"]),
                        detail=(
                            f"anomaly_months={result['summary']['anomaly_months']}, "
                            f"anomaly_txns={result['summary']['anomaly_transactions']}"
                        ),
                    )
                )
                return {
                    "columns": result["columns"],
                    "rows": result["rows"],
                    "row_count": len(result["rows"]),
                    "insights": result.get("insights") or [],
                    "anomalies": result.get("anomalies") or [],
                    "summary": result.get("summary"),
                    "sql": result["sql"],
                }
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
    choices_holder: list[dict[str, str]],
    insights_holder: list[dict[str, str]],
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
                choices_holder=choices_holder,
                insights_holder=insights_holder,
            )
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

        # If ambiguous accounts found, stop early — UI will show chips
        if len(choices_holder) > 1:
            labels = ", ".join(c["label"] for c in choices_holder[:5])
            return (
                f"I found multiple matching accounts ({labels}). "
                "Please pick one below so I don't guess the wrong account.\n"
                "STATUS: needs_clarification\nCONFIDENCE: medium"
            )

    return _synthesize_final_answer(
        client,
        model=model,
        contents=contents,
        user_message=user_message,
        evidence_holder=evidence_holder,
    )


def _maybe_precheck_ambiguity(user_message: str) -> tuple[list[dict[str, str]], str | None]:
    """Return clarification chips when multiple accounts match (don't guess)."""
    lower = user_message.lower()
    bank_match = re.search(
        r"\b(HDFC|ICIC|SBIN|UTIB|KKBK|CNRB|UBIN|AUBL|TMBL|RATN)\b",
        user_message,
        re.I,
    )
    bank_code = bank_match.group(1).upper() if bank_match else None

    last4 = None
    m4 = re.search(r"(?:ending(?:\s+in)?|last\s*4|xxxx|…|\.\.\.)\s*(\d{4})\b", user_message, re.I)
    if m4:
        last4 = m4.group(1)
    elif re.search(r"\baccount\b", lower):
        m = re.search(r"\b(\d{4})\b", user_message)
        if m:
            last4 = m.group(1)

    # Bank + balance/account without a specific id → offer chips if multiple
    wants_account = bool(
        re.search(r"\b(account|balance|balances|transactions?)\b", lower)
    )
    if not last4 and not (bank_code and wants_account):
        return [], None
    if bank_code and wants_account and not last4 and "account_id" in lower:
        return [], None

    db = SessionLocal()
    try:
        result = find_accounts(db, last4=last4, bank_code=bank_code)
    finally:
        db.close()

    matches = result.get("matches") or []
    if len(matches) <= 1:
        return [], None
    choices = matches_to_choices(matches)
    scope = f" ending {last4}" if last4 else ""
    bank_bit = f" at {bank_code}" if bank_code else ""
    answer = (
        f"I found {len(choices)} matching accounts{scope}{bank_bit}. "
        "Pick one chip below so I query the right account.\n"
        "STATUS: needs_clarification\nCONFIDENCE: medium"
    )
    return choices, answer


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
    choices_holder: list[dict[str, str]] = []
    insights_holder: list[dict[str, str]] = []

    if not retry:
        pre_choices, pre_answer = _maybe_precheck_ambiguity(user_message)
        if pre_choices and pre_answer:
            session_store.append_messages(
                session.session_id,
                [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": pre_answer},
                ],
            )
            return ChatResponse(
                session_id=session.session_id,
                answer=pre_answer,
                message=pre_answer,
                evidence=EvidenceTable(),
                tool_trace=[
                    ToolTraceItem(
                        tool="find_accounts",
                        ok=True,
                        row_count=len(pre_choices),
                        detail="precheck ambiguity",
                    )
                ],
                confidence="medium",
                status="needs_clarification",
                optimize_for=mode,  # type: ignore[arg-type]
                retried=False,
                choices=[ClarificationChoice(**c) for c in pre_choices],
                insights=[],
            )

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
            "or use analyze_debit_trends if it's a spend/growth question, then answer from new results."
        )

    import asyncio

    raw_answer = await asyncio.to_thread(
        _run_gemini_tool_loop,
        model=model,
        history_messages=history_messages,
        user_message=prompt_message,
        evidence_holder=evidence_holder,
        tool_trace=tool_trace,
        choices_holder=choices_holder,
        insights_holder=insights_holder,
    )

    answer, status, confidence = _infer_status(
        raw_answer,
        evidence_holder,
        tool_trace,
        choices=choices_holder,
    )
    evidence = EvidenceTable(
        columns=list(evidence_holder.get("columns") or []),
        rows=list(evidence_holder.get("rows") or []),
        sql=evidence_holder.get("sql"),
    )

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
        choices=[ClarificationChoice(**c) for c in choices_holder],
        insights=[InsightCallout(**i) for i in insights_holder],
    )
