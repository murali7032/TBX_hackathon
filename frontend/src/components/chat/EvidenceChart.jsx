import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceDot,
} from "recharts";

function isDateLike(value) {
  if (value == null) return false;
  const s = String(value);
  return /^\d{4}-\d{2}/.test(s) || !Number.isNaN(Date.parse(s));
}

function isNumeric(value) {
  if (value == null || value === "") return false;
  if (typeof value === "boolean") return false;
  const n = Number(value);
  return !Number.isNaN(n);
}

/** Build chart data; prefer total_debit + month; attach mom_pct / anomaly. */
export function buildTrendSeries(evidence) {
  if (!evidence?.columns?.length || !evidence?.rows?.length) return null;
  if (evidence.rows.length < 2) return null;

  const cols = evidence.columns.map((c) => String(c).toLowerCase());
  let xIdx = cols.findIndex((c) =>
    /date|month|day|week|period|time|year/.test(c)
  );
  let yIdx = cols.findIndex((c) =>
    /total_debit|transaction_amount|amount|sum|total|spend|debit|credit|value|balance/.test(
      c
    )
  );
  // Prefer total_debit over txn_count
  const totalDebitIdx = cols.indexOf("total_debit");
  if (totalDebitIdx >= 0) yIdx = totalDebitIdx;

  if (xIdx < 0) {
    xIdx = evidence.columns.findIndex((_, i) =>
      evidence.rows.every((r) => isDateLike(r[i]))
    );
  }
  if (yIdx < 0 || yIdx === xIdx) {
    yIdx = evidence.columns.findIndex(
      (_, i) =>
        i !== xIdx &&
        evidence.rows.every((r) => isNumeric(r[i]) && typeof r[i] !== "boolean")
    );
  }
  if (xIdx < 0 || yIdx < 0) return null;

  const momIdx = cols.findIndex((c) => /mom/.test(c));
  const anomIdx = cols.findIndex((c) => /anom|is_anomaly/.test(c));

  const data = evidence.rows.map((row) => {
    const rawX = row[xIdx];
    const label = String(rawX).replace("T", " ").slice(0, 10);
    const point = {
      label,
      value: Number(row[yIdx]),
      mom_pct: momIdx >= 0 && row[momIdx] != null ? Number(row[momIdx]) : null,
      is_anomaly: anomIdx >= 0 ? Boolean(row[anomIdx]) : false,
    };
    return point;
  });

  if (data.some((d) => Number.isNaN(d.value))) return null;
  return {
    data,
    xKey: "label",
    yKey: "value",
    xLabel: evidence.columns[xIdx],
    yLabel: evidence.columns[yIdx],
    hasMom: momIdx >= 0,
  };
}

export function shouldShowChart(userQuestion, evidence) {
  const series = buildTrendSeries(evidence);
  if (!series) return null;
  const q = (userQuestion || "").toLowerCase();
  const trendWords =
    /growth|trend|increas|decreas|over time|month|monthly|spend|spending|debit|mom|math|compar/;
  const cols = (evidence.columns || []).map((c) => String(c).toLowerCase());
  if (cols.includes("mom_pct_change") || cols.includes("is_anomaly")) return series;
  if (trendWords.test(q) || series.data.length >= 2) return series;
  return null;
}

function EvidenceChart({ evidence, userQuestion }) {
  const series = shouldShowChart(userQuestion, evidence);
  if (!series) return null;
  const anomalyPoints = series.data.filter((d) => d.is_anomaly);

  return (
    <div className="evidence-chart">
      <div className="evidence-title">
        Spend trend — {series.yLabel} by {series.xLabel}
        {series.hasMom ? " (with MoM %)" : ""}
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={series.data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip
              formatter={(value, name, props) => {
                if (name === "value") {
                  const mom = props?.payload?.mom_pct;
                  const base = Number(value).toLocaleString("en-IN");
                  if (mom == null || Number.isNaN(mom)) return [base, series.yLabel];
                  return [`${base} (MoM ${mom > 0 ? "+" : ""}${mom}%)`, series.yLabel];
                }
                return [value, name];
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              name={series.yLabel}
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
            {anomalyPoints.map((p) => (
              <ReferenceDot
                key={p.label}
                x={p.label}
                y={p.value}
                r={6}
                fill="#dc2626"
                stroke="#fff"
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      {anomalyPoints.length > 0 && (
        <div className="chart-anomaly-note">
          Red dots mark months with debits &gt; 2× median.
        </div>
      )}
    </div>
  );
}

export default EvidenceChart;
