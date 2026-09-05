import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "../api";

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [banks, setBanks] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([apiGet("/health"), apiGet("/api/banks")])
      .then(([h, b]) => {
        setHealth(h);
        setBanks(b);
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <p className="page-sub">Grounded finance data from Postgres + Cursor SDK chat.</p>
      {error && <p className="error-text">{error}</p>}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Banks</div>
          <div className="stat-value">{health?.banks ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Accounts</div>
          <div className="stat-value">{health?.accounts ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Transactions</div>
          <div className="stat-value">{health?.transactions ?? "—"}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Database</div>
          <div className="stat-value">{health?.database ?? "—"}</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">
          <h2>Banks</h2>
          <Link to="/banks">View all</Link>
        </div>
        <ul className="simple-list">
          {banks.slice(0, 5).map((bank) => (
            <li key={bank.bank_code}>
              <strong>{bank.bank_code}</strong> — {bank.bank_name}
            </li>
          ))}
        </ul>
      </div>

      <Link className="primary-link" to="/chat">
        Open chat assistant →
      </Link>
    </div>
  );
}

export default Dashboard;
