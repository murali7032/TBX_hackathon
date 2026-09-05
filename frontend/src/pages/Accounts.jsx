import { useEffect, useState } from "react";
import { apiGet } from "../api";

function maskAccount(num) {
  if (!num || num.length < 4) return "****";
  return `XXXX${num.slice(-4)}`;
}

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [bankFilter, setBankFilter] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const query = bankFilter ? `?bank_code=${encodeURIComponent(bankFilter)}` : "";
    apiGet(`/api/accounts${query}`)
      .then(setAccounts)
      .catch((err) => setError(err.message));
  }, [bankFilter]);

  return (
    <div className="page">
      <h1>Accounts</h1>
      <p className="page-sub">Account balances and bank linkage — numbers masked for privacy.</p>
      <div className="filters">
        <input
          placeholder="Filter by bank code (e.g. HDFC)"
          value={bankFilter}
          onChange={(e) => setBankFilter(e.target.value.toUpperCase())}
        />
      </div>
      {error && <p className="error-text">{error}</p>}
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Account</th>
              <th>Bank</th>
              <th>Program</th>
              <th>Balance</th>
              <th>Number</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((acc) => (
              <tr key={acc.account_id}>
                <td className="mono">{acc.account_id.slice(0, 8)}…</td>
                <td>{acc.bank_code}</td>
                <td>{acc.program_id}</td>
                <td>{formatMoney(acc.available_balance)}</td>
                <td>{maskAccount(acc.account_number)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Accounts;
