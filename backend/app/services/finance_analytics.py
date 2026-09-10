"""Deterministic finance analytics helpers for the chat agent (MySQL)."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from statistics import median
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

PeriodName = Literal["this_month", "last_month", "last_30_days", "all"]
TxnTypeFilter = Literal["debit", "credit", "all"]

# Short stems that match rail noise inside narrations (e.g. NET → INET).
_BLOCKED_SHORT_TOKENS = frozenset({"NET", "FLI", "INE", "IMP", "NEF"})


def _sanitize_keywords(keywords: list[str] | None, *, min_len: int = 4) -> list[str]:
    """Uppercase, dedupe, drop stems shorter than min_len (stops NET→INET)."""
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in keywords or []:
        token = re.sub(r"[^A-Za-z0-9]+", "", str(raw).strip()).upper()
        if not token or token in seen:
            continue
        if len(token) < min_len:
            continue
        if token in _BLOCKED_SHORT_TOKENS and len(token) < 5:
            continue
        seen.add(token)
        cleaned.append(token)
    return cleaned


def _period_bounds(period: str) -> tuple[datetime | None, datetime | None, str]:
    """Return [start, end) datetime bounds and a label. end is exclusive."""
    today = date.today()
    p = (period or "this_month").strip().lower()
    if p == "all":
        return None, None, "all"
    if p == "last_30_days":
        start = datetime.combine(today - timedelta(days=30), datetime.min.time())
        end = datetime.combine(today + timedelta(days=1), datetime.min.time())
        return start, end, "last_30_days"
    if p == "last_month":
        first_this = today.replace(day=1)
        last_month_end = first_this
        if first_this.month == 1:
            last_month_start = first_this.replace(year=first_this.year - 1, month=12)
        else:
            last_month_start = first_this.replace(month=first_this.month - 1)
        return (
            datetime.combine(last_month_start, datetime.min.time()),
            datetime.combine(last_month_end, datetime.min.time()),
            "last_month",
        )
    # this_month (default)
    start_d = today.replace(day=1)
    if start_d.month == 12:
        end_d = start_d.replace(year=start_d.year + 1, month=1)
    else:
        end_d = start_d.replace(month=start_d.month + 1)
    return (
        datetime.combine(start_d, datetime.min.time()),
        datetime.combine(end_d, datetime.min.time()),
        "this_month",
    )


def summarize_merchant_spend(
    db: Session,
    *,
    keywords: list[str] | None = None,
    period: PeriodName | str = "this_month",
    transaction_type: TxnTypeFilter | str = "debit",
) -> dict[str, Any]:
    """Aggregate COUNT/SUM for merchant-like description matches in a date window."""
    tokens = _sanitize_keywords(keywords)
    if not tokens:
        return {
            "error": (
                "Provide keywords of at least 4 alphanumeric characters "
                "(e.g. NETFLIX, not NET). Short stems match rail noise like INET."
            ),
            "columns": [],
            "rows": [],
            "sql": None,
        }

    start, end, period_label = _period_bounds(str(period))
    type_filter = (transaction_type or "debit").strip().lower()
    if type_filter not in {"debit", "credit", "all"}:
        type_filter = "debit"

    clauses: list[str] = []
    params: dict[str, Any] = {}

    if type_filter != "all":
        clauses.append("transaction_type = :txn_type")
        params["txn_type"] = type_filter

    if start is not None and end is not None:
        clauses.append("transaction_date >= :start_ts")
        clauses.append("transaction_date < :end_ts")
        params["start_ts"] = start
        params["end_ts"] = end

    like_parts: list[str] = []
    for i, token in enumerate(tokens):
        key = f"kw{i}"
        like_parts.append(f"description LIKE :{key}")
        params[key] = f"%{token}%"
    clauses.append("(" + " OR ".join(like_parts) + ")")

    where = " AND ".join(clauses)
    sql = f"""
SELECT
  COUNT(*) AS txn_count,
  COALESCE(SUM(transaction_amount), 0) AS total_amount,
  MIN(transaction_date) AS first_txn,
  MAX(transaction_date) AS last_txn
FROM `transaction`
WHERE {where}
""".strip()

    row = db.execute(text(sql), params).fetchone()
    txn_count = int(row.txn_count) if row and row.txn_count is not None else 0
    total = float(row.total_amount) if row and row.total_amount is not None else 0.0
    first_txn = (
        row.first_txn.isoformat()
        if row and row.first_txn is not None and hasattr(row.first_txn, "isoformat")
        else (str(row.first_txn) if row and row.first_txn is not None else None)
    )
    last_txn = (
        row.last_txn.isoformat()
        if row and row.last_txn is not None and hasattr(row.last_txn, "isoformat")
        else (str(row.last_txn) if row and row.last_txn is not None else None)
    )

    columns = [
        "txn_count",
        "total_amount",
        "first_txn",
        "last_txn",
        "period",
        "transaction_type",
        "keywords",
    ]
    rows = [
        [
            txn_count,
            round(total, 2),
            first_txn,
            last_txn,
            period_label,
            type_filter,
            ", ".join(tokens),
        ]
    ]

    return {
        "columns": columns,
        "rows": rows,
        "sql": sql,
        "summary": {
            "txn_count": txn_count,
            "total_amount": round(total, 2),
            "period": period_label,
            "transaction_type": type_filter,
            "keywords": tokens,
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        },
        "hint": (
            None
            if txn_count > 0
            else "No matching transactions in this period. Try broader keywords (still ≥4 chars) or period=all."
        ),
    }


def find_accounts(
    db: Session,
    *,
    last4: str | None = None,
    bank_code: str | None = None,
    account_number: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Search accounts for ambiguity resolution (masked labels for UI chips)."""
    clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit}

    if last4:
        digits = "".join(ch for ch in last4 if ch.isdigit())[-4:]
        if len(digits) != 4:
            return {"matches": [], "error": "last4 must be 4 digits"}
        clauses.append("RIGHT(account_number, 4) = :last4")
        params["last4"] = digits

    if bank_code:
        clauses.append("UPPER(bank_code) = :bank_code")
        params["bank_code"] = bank_code.strip().upper()

    if account_number:
        clauses.append("account_number LIKE :account_number")
        params["account_number"] = f"%{account_number.strip()}%"

    if not clauses:
        return {"matches": [], "error": "Provide last4, bank_code, and/or account_number"}

    where = " AND ".join(clauses)
    rows = db.execute(
        text(
            f"""
            SELECT account_id, entity_id, account_number, program_id,
                   available_balance, bank_code
            FROM account
            WHERE {where}
            ORDER BY bank_code, account_number
            LIMIT :limit
            """
        ),
        params,
    ).fetchall()

    matches = []
    for row in rows:
        last = str(row.account_number)[-4:]
        label = f"Account ...{last} ({row.bank_code})"
        matches.append(
            {
                "account_id": row.account_id,
                "entity_id": row.entity_id,
                "bank_code": row.bank_code,
                "last4": last,
                "available_balance": float(row.available_balance),
                "program_id": row.program_id,
                "label": label,
                "follow_up": (
                    f"Show balance and recent transactions for account_id "
                    f"{row.account_id} ({label})"
                ),
            }
        )

    return {
        "match_count": len(matches),
        "ambiguous": len(matches) > 1,
        "matches": matches,
        "hint": (
            "Multiple accounts matched. Ask the user to pick one chip; do not guess."
            if len(matches) > 1
            else None
        ),
    }


DEBIT_MOM_SQL = """
WITH monthly AS (
  SELECT
    DATE_FORMAT(transaction_date, '%Y-%m-01') AS month,
    COUNT(*) AS txn_count,
    SUM(transaction_amount) AS total_debit
  FROM `transaction`
  WHERE transaction_type = 'debit'
    AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 36 MONTH)
  GROUP BY DATE_FORMAT(transaction_date, '%Y-%m-01')
),
with_lag AS (
  SELECT
    month,
    txn_count,
    total_debit,
    LAG(total_debit) OVER (ORDER BY month) AS prev_month_debit,
    ROUND(
      (
        (total_debit - LAG(total_debit) OVER (ORDER BY month))
        / NULLIF(LAG(total_debit) OVER (ORDER BY month), 0)
      ) * 100,
      2
    ) AS mom_pct_change
  FROM monthly
)
SELECT
  month,
  txn_count,
  total_debit,
  prev_month_debit,
  mom_pct_change
FROM with_lag
ORDER BY month
"""


DEBIT_TXN_ANOMALY_SQL = """
SELECT
  transaction_id,
  account_id,
  transaction_date,
  transaction_amount,
  LEFT(COALESCE(description, ''), 80) AS description
FROM `transaction`
WHERE transaction_type = 'debit'
  AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 36 MONTH)
ORDER BY transaction_amount DESC
LIMIT 50
"""


def analyze_debit_trends(db: Session) -> dict[str, Any]:
    """MoM debit totals + anomaly flags (month > 2× median)."""
    month_rows = db.execute(text(DEBIT_MOM_SQL)).fetchall()
    columns = [
        "month",
        "txn_count",
        "total_debit",
        "prev_month_debit",
        "mom_pct_change",
        "median_monthly_debit",
        "is_anomaly",
    ]
    totals = [
        float(r.total_debit)
        for r in month_rows
        if r.total_debit is not None
    ]
    median_monthly = float(median(totals)) if totals else None

    rows: list[list[Any]] = []
    insights: list[str] = []
    anomalies: list[dict[str, Any]] = []

    for r in month_rows:
        month = r.month.isoformat() if hasattr(r.month, "isoformat") else str(r.month)
        total = float(r.total_debit) if r.total_debit is not None else None
        prev = float(r.prev_month_debit) if r.prev_month_debit is not None else None
        mom = float(r.mom_pct_change) if r.mom_pct_change is not None else None
        is_anom = bool(
            total is not None
            and median_monthly is not None
            and median_monthly > 0
            and total > 2 * median_monthly
        )
        rows.append(
            [
                month,
                int(r.txn_count),
                total,
                prev,
                mom,
                round(median_monthly, 2) if median_monthly is not None else None,
                is_anom,
            ]
        )
        if is_anom and total is not None and median_monthly is not None:
            anomalies.append(
                {
                    "type": "month",
                    "month": month,
                    "total_debit": total,
                    "median": median_monthly,
                    "message": (
                        f"Anomaly: {month} debits ₹{total:,.2f} are > 2× "
                        f"median monthly debit ₹{median_monthly:,.2f}."
                    ),
                }
            )
            insights.append(anomalies[-1]["message"])
        if mom is not None:
            direction = "up" if mom > 0 else "down" if mom < 0 else "flat"
            insights.append(
                f"{month}: MoM debit change {mom:+.2f}% ({direction}) vs prior month."
            )

    txn_rows = db.execute(text(DEBIT_TXN_ANOMALY_SQL)).fetchall()
    amounts = [float(t.transaction_amount) for t in txn_rows if t.transaction_amount is not None]
    median_txn = float(median(amounts)) if amounts else None
    txn_anomalies = []
    if median_txn and median_txn > 0:
        for t in txn_rows:
            amount = float(t.transaction_amount)
            if amount <= 2 * median_txn:
                continue
            vs = round(amount / median_txn, 2)
            msg = (
                f"Large txn {t.transaction_id[:8]}… amount ₹{amount:,.2f} "
                f"is {vs:.1f}× median debit ₹{median_txn:,.2f}."
            )
            txn_anomalies.append(
                {
                    "type": "transaction",
                    "transaction_id": t.transaction_id,
                    "amount": amount,
                    "vs_median_x": vs,
                    "message": msg,
                }
            )
            insights.append(msg)
            if len(txn_anomalies) >= 10:
                break

    return {
        "columns": columns,
        "rows": rows,
        "sql": DEBIT_MOM_SQL.strip(),
        "anomalies": anomalies + txn_anomalies,
        "insights": insights[-12:],
        "summary": {
            "months": len(rows),
            "anomaly_months": sum(1 for row in rows if row[6]),
            "anomaly_transactions": len(txn_anomalies),
        },
    }


def matches_to_choices(matches: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "id": m["account_id"],
            "label": m["label"],
            "follow_up": m["follow_up"],
        }
        for m in matches[:5]
    ]
