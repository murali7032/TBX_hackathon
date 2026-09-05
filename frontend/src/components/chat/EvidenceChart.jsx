import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

function isDateLike(value) {
  if (value == null) return false;
  const s = String(value);
  return /^\d{4}-\d{2}/.test(s) || !Number.isNaN(Date.parse(s));
}

function isNumeric(value) {
  if (value == null || value === "") return false;
  const n = Number(value);
  return !Number.isNaN(n);
}

/** Build chart data when evidence looks like a time series (date + number). */
export function buildTrendSeries(evidence) {
  if (!evidence?.columns?.length || !evidence?.rows?.length) return null;
  if (evidence.rows.length < 2) return null;

  const cols = evidence.columns.map((c) => String(c).toLowerCase());
  let xIdx = cols.findIndex((c) =>
    /date|month|day|week|period|time|year/.test(c)
  );
  let yIdx = cols.findIndex((c) =>
    /amount|sum|total|count|balance|spend|debit|credit|value/.test(c)
  );

  if (xIdx < 0) {
    xIdx = evidence.columns.findIndex((_, i) =>
      evidence.rows.every((r) => isDateLike(r[i]))
    );
  }
  if (yIdx < 0 || yIdx === xIdx) {
    yIdx = evidence.columns.findIndex(
      (_, i) => i !== xIdx && evidence.rows.every((r) => isNumeric(r[i]))
    );
  }
  if (xIdx < 0 || yIdx < 0) return null;

  const data = evidence.rows.map((row) => {
    const rawX = row[xIdx];
    const label = String(rawX).replace("T", " ").slice(0, 10);
    return {
      label,
      value: Number(row[yIdx]),
    };
  });

  if (data.some((d) => Number.isNaN(d.value))) return null;
  return {
    data,
    xKey: "label",
    yKey: "value",
    xLabel: evidence.columns[xIdx],
    yLabel: evidence.columns[yIdx],
  };
}

export function shouldShowChart(userQuestion, evidence) {
  const series = buildTrendSeries(evidence);
  if (!series) return false;
  const q = (userQuestion || "").toLowerCase();
  const trendWords =
    /growth|trend|increas|decreas|over time|month|monthly|spend|spending|debit|credit|compar|how much/;
  // Show when question is trend-like OR evidence is clearly time-series with 2+ points
  return trendWords.test(q) || series.data.length >= 2;
}

function EvidenceChart({ evidence, userQuestion }) {
  if (!shouldShowChart(userQuestion, evidence)) return null;
  const series = buildTrendSeries(evidence);
  if (!series) return null;

  return (
    <div className="evidence-chart">
      <div className="evidence-title">
        Trend — {series.yLabel} by {series.xLabel}
      </div>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={series.data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="value"
              name={series.yLabel}
              stroke="#2563eb"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default EvidenceChart;
