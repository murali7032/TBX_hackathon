from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models import TransactionType


class BankOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bank_code: str
    bank_name: str


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    entity_id: str
    account_number: str
    program_id: int
    available_balance: Decimal
    bank_code: str


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    account_id: str
    transaction_date: datetime
    transaction_type: TransactionType
    description: str | None = None
    transaction_amount: Decimal
    transaction_reference_id: str | None = None
    utr_number: str | None = None


class HealthOut(BaseModel):
    status: str = "ok"
    database: str
    banks: int = Field(ge=0)
    accounts: int = Field(ge=0)
    transactions: int = Field(ge=0)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    optimize_for: Literal["cost", "balanced", "intelligence"] | None = None
    retry: bool = False
    previous_sql: str | None = None
    previous_answer: str | None = None


class FeedbackRequest(BaseModel):
    session_id: str
    rating: Literal["up", "down"]
    message: str = Field(min_length=1, max_length=4000)
    previous_sql: str | None = None
    previous_answer: str | None = None
    optimize_for: Literal["cost", "balanced", "intelligence"] | None = None


class ClarificationChoice(BaseModel):
    id: str
    label: str
    follow_up: str


class InsightCallout(BaseModel):
    type: str = "info"
    message: str


class EvidenceTable(BaseModel):
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    sql: str | None = None


class ToolTraceItem(BaseModel):
    tool: str
    ok: bool = True
    sql: str | None = None
    row_count: int | None = None
    detail: str | None = None
    duration_ms: float | None = None


class LatencyRound(BaseModel):
    round: int
    llm_ms: float = 0
    tool_ms: float = 0
    tools: list[str] = Field(default_factory=list)


class LatencyBreakdown(BaseModel):
    total_ms: float = 0
    llm_ms: float = 0
    sql_ms: float = 0
    tool_ms: float = 0
    postprocess_ms: float = 0
    rounds: list[LatencyRound] = Field(default_factory=list)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    # Frontend-compatible aliases (finance-assistant Chat.jsx)
    message: str
    type: str = "text"
    data: dict[str, Any] | None = None
    evidence: EvidenceTable
    tool_trace: list[ToolTraceItem]
    confidence: Literal["high", "medium", "low"] = "medium"
    status: Literal["answered", "needs_clarification", "insufficient_data"] = "answered"
    optimize_for: Literal["cost", "balanced", "intelligence"] | None = None
    retried: bool = False
    choices: list[ClarificationChoice] = Field(default_factory=list)
    insights: list[InsightCallout] = Field(default_factory=list)
    latency: LatencyBreakdown | None = None


class ChatHistoryMessage(BaseModel):
    role: str
    content: str


class ChatSessionOut(BaseModel):
    session_id: str
    messages: list[ChatHistoryMessage]


class SqlRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=8000)


class SqlResponse(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    sql: str


class ExportRequest(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    filename: str = "evidence.csv"
