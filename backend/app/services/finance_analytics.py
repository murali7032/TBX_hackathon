"""Deterministic finance analytics helpers for the chat agent."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


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
        clauses.append("account_number ILIKE :account_number")
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
    date_trunc('month', transaction_date)::date AS month,
    COUNT(*)::int AS txn_count,
    SUM(transaction_amount)::numeric AS total_debit
  FROM "transaction"
  WHERE transaction_type = 'debit'
  GROUP BY 1
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
),
stats AS (
  SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_debit) AS median_debit
  FROM monthly
)
SELECT
  w.month,
  w.txn_count,
  w.total_debit,
  w.prev_month_debit,
  w.mom_pct_change,
  ROUND(s.median_debit::numeric, 2) AS median_monthly_debit,
  CASE
    WHEN w.total_debit > 2 * s.median_debit THEN true
    ELSE false
  END AS is_anomaly
FROM with_lag w
CROSS JOIN stats s
ORDER BY w.month
"""


DEBIT_TXN_ANOMALY_SQL = """
WITH debits AS (
  SELECT
    transaction_id,
    account_id,
    transaction_date,
    transaction_amount,
    LEFT(COALESCE(description, ''), 80) AS description
  FROM "transaction"
  WHERE transaction_type = 'debit'
),
stats AS (
  SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY transaction_amount) AS median_amt
  FROM debits
)
SELECT
  d.transaction_id,
  d.account_id,
  d.transaction_date,
  d.transaction_amount,
  d.description,
  ROUND(s.median_amt::numeric, 2) AS median_debit,
  ROUND((d.transaction_amount / NULLIF(s.median_amt, 0))::numeric, 2) AS vs_median_x
FROM debits d
CROSS JOIN stats s
WHERE d.transaction_amount > 2 * s.median_amt
ORDER BY d.transaction_amount DESC
LIMIT 10
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
    rows: list[list[Any]] = []
    insights: list[str] = []
    anomalies: list[dict[str, Any]] = []

    for r in month_rows:
        month = r.month.isoformat() if hasattr(r.month, "isoformat") else str(r.month)
        total = float(r.total_debit) if r.total_debit is not None else None
        prev = float(r.prev_month_debit) if r.prev_month_debit is not None else None
        mom = float(r.mom_pct_change) if r.mom_pct_change is not None else None
        median = float(r.median_monthly_debit) if r.median_monthly_debit is not None else None
        is_anom = bool(r.is_anomaly)
        rows.append([month, int(r.txn_count), total, prev, mom, median, is_anom])
        if is_anom and total is not None and median is not None:
            anomalies.append(
                {
                    "type": "month",
                    "month": month,
                    "total_debit": total,
                    "median": median,
                    "message": (
                        f"Anomaly: {month} debits ₹{total:,.2f} are > 2× "
                        f"median monthly debit ₹{median:,.2f}."
                    ),
                }
            )
            insights.append(anomalies[-1]["message"])
        if mom is not None:
            direction = "up" if mom > 0 else "down" if mom < 0 else "flat"
            insights.append(
                f"{month}: MoM debit change {mom:+.2f}% ({direction}) vs prior month."
            )

    txn_anom = db.execute(text(DEBIT_TXN_ANOMALY_SQL)).fetchall()
    txn_anomalies = []
    for t in txn_anom:
        msg = (
            f"Large txn {t.transaction_id[:8]}… amount ₹{float(t.transaction_amount):,.2f} "
            f"is {float(t.vs_median_x):.1f}× median debit ₹{float(t.median_debit):,.2f}."
        )
        txn_anomalies.append(
            {
                "type": "transaction",
                "transaction_id": t.transaction_id,
                "amount": float(t.transaction_amount),
                "vs_median_x": float(t.vs_median_x),
                "message": msg,
            }
        )
        insights.append(msg)

    return {
        "columns": columns,
        "rows": rows,
        "sql": DEBIT_MOM_SQL.strip(),
        "anomalies": anomalies + txn_anomalies,
        "insights": insights[-12:],  # keep prompt compact
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
