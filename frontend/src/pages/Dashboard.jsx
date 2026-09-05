import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiGet } from "../api";
import PageLoader from "../components/PageLoader";

function formatMoney(value) {
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return n.toLocaleString("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function shortLabel(text, max = 18) {
  const s = String(text || "Unknown");
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

function aggregateDashboard(accounts, banks, transactions) {
  const bankNameByCode = Object.fromEntries(
    (banks || []).map((b) => [b.bank_code, b.bank_name || b.bank_code])
  );
  const accountBank = Object.fromEntries(
    (accounts || []).map((a) => [a.account_id, a.bank_code])
  );

  let debit = 0;
  let credit = 0;
  let minDate = null;
  let maxDate = null;
  const byBank = new Map();
  const byPayee = new Map();

  for (const txn of transactions || []) {
    const amount = Number(txn.transaction_amount) || 0;
    const type = String(txn.transaction_type || "").toLowerCase();
    const date = txn.transaction_date ? new Date(txn.transaction_date) : null;
    if (date && !Number.isNaN(date.getTime())) {
      if (!minDate || date < minDate) minDate = date;
      if (!maxDate || date > maxDate) maxDate = date;
    }

    if (type === "debit") {
      debit += amount;
      const bankCode = accountBank[txn.account_id] || "OTHER";
      const bankLabel = bankNameByCode[bankCode] || bankCode;
      const bankRow = byBank.get(bankCode) || {
        key: bankCode,
        group: bankLabel,
        transactions: 0,
        amount: 0,
      };
      bankRow.transactions += 1;
      bankRow.amount += amount;
      byBank.set(bankCode, bankRow);

      const payee =
        (txn.description && String(txn.description).trim()) || "Unlabeled payee";
      const payeeRow = byPayee.get(payee) || {
        key: payee,
        group: payee,
        transactions: 0,
        amount: 0,
      };
      payeeRow.transactions += 1;
      payeeRow.amount += amount;
      byPayee.set(payee, payeeRow);
    } else if (type === "credit") {
      credit += amount;
    }
  }

  const sortDesc = (a, b) => b.amount - a.amount;
  const spendByBank = [...byBank.values()].sort(sortDesc);
  const topPayees = [...byPayee.values()].sort(sortDesc).slice(0, 6);
  const bankMax = spendByBank[0]?.amount || 1;
  const payeeMax = topPayees[0]?.amount || 1;

  return {
    debit,
    credit,
    txnCount: (transactions || []).length,
    accountCount: (accounts || []).length,
    bankCount: (banks || []).length,
    minDate,
    maxDate,
    spendByBank: spendByBank.map((row) => ({
      ...row,
      share: row.amount / bankMax,
      chartLabel: shortLabel(row.group, 16),
    })),
    topPayees: topPayees.map((row) => ({
      ...row,
      share: row.amount / payeeMax,
      chartLabel: shortLabel(row.group, 16),
    })),
  };
}

function MetricCard({ label, value }) {
  return (
    <div className="stat-card dash-metric">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  );
}

function ShareTable({ rows }) {
  if (!rows?.length) {
    return <p className="dash-empty">No debit activity in the loaded window.</p>;
  }
  return (
    <div className="dash-share-table">
      <div className="dash-share-head">
        <span>Group</span>
        <span>Transactions</span>
        <span>Amount</span>
      </div>
      {rows.map((row) => (
        <div className="dash-share-row" key={row.key}>
          <div className="dash-share-group">
            <strong>{row.group}</strong>
            <div className="dash-share-bar-track">
              <div
                className="dash-share-bar-fill"
                style={{ width: `${Math.max(6, row.share * 100)}%` }}
              />
            </div>
          </div>
          <div className="dash-share-count">{row.transactions}</div>
          <div className="dash-share-amount">{formatMoney(row.amount)}</div>
        </div>
      ))}
    </div>
  );
}

function AnalysisCard({ title, askHref, chartData, tableRows }) {
  return (
    <section className="dash-card">
      <div className="dash-card-header">
        <h2>{title}</h2>
        <Link className="ask-link" to={askHref}>
          Ask about this
        </Link>
      </div>
      <div className="dash-chart">
        {chartData.length === 0 ? (
          <p className="dash-empty">Nothing to chart yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 12, left: 8, bottom: 4 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
              <XAxis
                type="number"
                tickFormatter={(v) =>
                  Number(v).toLocaleString("en-IN", { notation: "compact" })
                }
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="chartLabel"
                width={108}
                tick={{ fill: "#334155", fontSize: 11, fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                formatter={(value) => formatMoney(value)}
                labelFormatter={(label) => label}
                contentStyle={{
                  borderRadius: 10,
                  border: "1px solid #e2e8f0",
                  fontFamily: "Montserrat, sans-serif",
                  fontSize: 12,
                }}
              />
              <Bar dataKey="amount" fill="#0b1f3a" radius={[0, 6, 6, 0]} barSize={14} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      <ShareTable rows={tableRows} />
    </section>
  );
}

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [banks, setBanks] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiGet("/health"),
      apiGet("/api/banks"),
      apiGet("/api/accounts"),
      apiGet("/api/transactions?limit=500"),
    ])
      .then(([h, b, a, t]) => {
        setHealth(h);
        setBanks(b);
        setAccounts(a);
        setTransactions(t);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const summary = useMemo(
    () => aggregateDashboard(accounts, banks, transactions),
    [accounts, banks, transactions]
  );

  const dateRangeLabel =
    summary.minDate && summary.maxDate
      ? `${formatDate(summary.minDate)} – ${formatDate(summary.maxDate)}`
      : "Loaded ledger window";

  return (
    <div className="page dashboard-page">
      <header className="dash-topbar">
        <div className="dash-topbar-copy">
          <p className="page-kicker">TBX Finance</p>
          <h1>Dashboard</h1>
          <p className="page-sub dash-tagline">
            Corporate Banking Infrastructure
            <br />
            for a Connected Financial Ecosystem
          </p>
          <p className="dash-caption">
            Workspace totals from loaded bank, account, and transaction tables.
          </p>
        </div>
        <div className="dash-topbar-actions">
          <div className="dash-pill" title="Derived from transaction dates">
            <span className="dash-pill-icon" aria-hidden="true">
              ▦
            </span>
            {dateRangeLabel}
          </div>
          <div className="dash-profile" title="Demo persona">
            <div className="dash-avatar">FM</div>
            <div className="dash-profile-text">
              <strong>Finance manager</strong>
              <span>TBX demo workspace</span>
            </div>
          </div>
        </div>
      </header>

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <PageLoader
          label="Preparing dashboard…"
          hint="Aggregating banks, accounts, and transactions"
        />
      ) : (
        <>
      <div className="stat-grid dash-metrics">
        <MetricCard label="Debit spend" value={formatMoney(summary.debit)} />
        <MetricCard label="Credits" value={formatMoney(summary.credit)} />
        <MetricCard
          label="Transactions"
          value={health?.transactions ?? summary.txnCount ?? "—"}
        />
        <MetricCard
          label="Accounts"
          value={health?.accounts ?? summary.accountCount ?? "—"}
        />
      </div>

      <p className="dash-coverage">
        Coverage: {summary.bankCount || health?.banks || 0} banks ·{" "}
        {summary.accountCount || 0} accounts in view · {summary.txnCount} transactions
        loaded for analysis
      </p>

      <div className="dash-grid">
        <AnalysisCard
          title="Spend by bank"
          askHref="/chat"
          chartData={summary.spendByBank}
          tableRows={summary.spendByBank}
        />
        <AnalysisCard
          title="Top payees"
          askHref="/chat"
          chartData={summary.topPayees}
          tableRows={summary.topPayees}
        />
      </div>

      <div className="dash-footer-row">
        <Link className="primary-link" to="/chat">
          Ask TBX Insight →
        </Link>
        <Link className="dash-secondary-link" to="/banks">
          Browse banks
        </Link>
      </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
