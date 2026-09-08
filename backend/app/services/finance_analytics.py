"""Deterministic finance analytics helpers for the chat agent (MySQL)."""

from __future__ import annotations

from statistics import median
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
