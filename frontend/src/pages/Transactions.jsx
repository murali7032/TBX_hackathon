import { useEffect, useState } from "react";
import { apiGet } from "../api";

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function Transactions() {
  const [rows, setRows] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams({ limit: "50" });
    if (typeFilter) params.set("transaction_type", typeFilter);
    apiGet(`/api/transactions?${params}`)
      .then(setRows)
      .catch((err) => setError(err.message));
  }, [typeFilter]);

  return (
    <div className="page">
      <h1>Transactions</h1>
      <p className="page-sub">Credits and debits from the finance dataset.</p>
      <div className="filters">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">All types</option>
          <option value="credit">credit</option>
          <option value="debit">debit</option>
        </select>
      </div>
      {error && <p className="error-text">{error}</p>}
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Amount</th>
              <th>Ref</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((txn) => (
              <tr key={txn.transaction_id}>
                <td>{String(txn.transaction_date).replace("T", " ").slice(0, 19)}</td>
                <td>{txn.transaction_type}</td>
                <td>{formatMoney(txn.transaction_amount)}</td>
                <td className="mono">{txn.transaction_reference_id || "—"}</td>
                <td className="desc">{txn.description || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Transactions;
