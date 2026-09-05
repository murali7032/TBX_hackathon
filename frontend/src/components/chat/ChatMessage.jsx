import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import EvidenceChart from "./EvidenceChart";

/** Parse first GitHub-flavored markdown table into {columns, rows}. */
export function parseMarkdownTable(text) {
  if (!text || typeof text !== "string") return null;
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  const isSep = (line) =>
    /^\|?(\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?$/.test(line);

  for (let i = 0; i < lines.length - 1; i += 1) {
    const headerLine = lines[i];
    const sepLine = lines[i + 1];
    if (!headerLine.includes("|") || !isSep(sepLine)) continue;

    const splitRow = (line) =>
      line
        .replace(/^\|/, "")
        .replace(/\|$/, "")
        .split("|")
        .map((c) => c.trim());

    const columns = splitRow(headerLine);
    if (columns.length < 1) continue;
    const rows = [];
    for (let j = i + 2; j < lines.length; j += 1) {
      if (!lines[j].includes("|")) break;
      const cells = splitRow(lines[j]);
      if (cells.length === 0) break;
      while (cells.length < columns.length) cells.push("");
      rows.push(cells.slice(0, columns.length));
    }
    if (rows.length > 0) return { columns, rows, sql: null };
  }
  return null;
}

function resolveTable(evidence, answerText) {
  if (evidence?.columns?.length && (evidence.rows?.length || 0) >= 0) {
    return {
      columns: evidence.columns,
      rows: evidence.rows || [],
      sql: evidence.sql || null,
    };
  }
  return parseMarkdownTable(answerText);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function escapeCsvCell(value) {
  const s = value == null ? "" : String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

function exportTableCsv(columns, rows, filename = "chat-export.csv") {
  const lines = [
    columns.map(escapeCsvCell).join(","),
    ...rows.map((row) => row.map(escapeCsvCell).join(",")),
  ];
  const blob = new Blob(["\uFEFF" + lines.join("\n")], {
    type: "text/csv;charset=utf-8;",
  });
  downloadBlob(blob, filename);
}

/** Excel-openable HTML workbook (no server required). */
function exportTableExcel(columns, rows, filename = "chat-export.xls") {
  const esc = (v) =>
    String(v ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  const head = columns.map((c) => `<th>${esc(c)}</th>`).join("");
  const body = rows
    .map((row) => `<tr>${row.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`)
    .join("");
  const html = `<!DOCTYPE html><html><head><meta charset="utf-8" /></head><body><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></body></html>`;
  const blob = new Blob([html], {
    type: "application/vnd.ms-excel;charset=utf-8;",
  });
  downloadBlob(blob, filename);
}

function ExportButtons({ columns, rows }) {
  if (!columns?.length) return null;
  return (
    <div className="export-bar">
      <span className="export-label">Export table</span>
      <button
        type="button"
        className="export-btn"
        onClick={() => exportTableCsv(columns, rows)}
      >
        Export CSV
      </button>
      <button
        type="button"
        className="export-btn export-btn-primary"
        onClick={() => exportTableExcel(columns, rows)}
      >
        Export Excel
      </button>
    </div>
  );
}

function EvidenceBlock({ evidence, userQuestion, answerText }) {
  const table = resolveTable(evidence, answerText);
  if (!table?.columns?.length) return null;
  const rows = table.rows || [];

  return (
    <div className="evidence-block">
      <div className="evidence-header">
        <div className="evidence-title">Results table</div>
        <ExportButtons columns={table.columns} rows={rows} />
      </div>
      {table.sql && <pre className="evidence-sql">{table.sql}</pre>}
      <EvidenceChart
        evidence={{ columns: table.columns, rows }}
        userQuestion={userQuestion}
      />
      <div className="evidence-table-wrap">
        <table className="evidence-table">
          <thead>
            <tr>
              {table.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((row, idx) => (
              <tr key={idx}>
                {row.map((cell, cIdx) => (
                  <td key={cIdx}>{cell === null ? "—" : String(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ExportButtons columns={table.columns} rows={rows} />
    </div>
  );
}

function FeedbackBar({
  feedback,
  onThumbsUp,
  onThumbsDown,
  disabled,
}) {
  return (
    <div className="feedback-bar">
      <span className="feedback-label">Was this helpful?</span>
      <button
        type="button"
        className={`feedback-btn ${feedback === "up" ? "active" : ""}`}
        onClick={onThumbsUp}
        disabled={disabled || feedback === "up"}
        title="Thumbs up"
      >
        👍
      </button>
      <button
        type="button"
        className={`feedback-btn ${feedback === "down" ? "active" : ""}`}
        onClick={onThumbsDown}
        disabled={disabled || feedback === "down"}
        title="Thumbs down — regenerate with a new SQL query"
      >
        👎
      </button>
      {feedback === "up" && (
        <span className="feedback-note">Thanks for the feedback</span>
      )}
      {feedback === "down" && (
        <span className="feedback-note">Regenerating with a new query…</span>
      )}
    </div>
  );
}

function ChatMessage({
  message,
  children,
  onThumbsUp,
  onThumbsDown,
  feedbackDisabled,
}) {
  const isUser = message?.role === "user";
  const text = typeof message?.text === "string" ? message.text : "";
  const hasStructuredTable =
    Boolean(message?.evidence?.columns?.length) ||
    Boolean(parseMarkdownTable(text));

  return (
    <div
      className={
        isUser ? "chat-message user-message" : "chat-message assistant-message"
      }
    >
      <div className="chat-message-avatar">{isUser ? "You" : "✦"}</div>

      <div className="chat-message-content">
        {children ? (
          children
        ) : isUser ? (
          <div className="user-message-text">{text}</div>
        ) : (
          <>
            {message?.retried && (
              <div className="retry-badge">Regenerated after feedback</div>
            )}
            {text && (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
            )}
            <EvidenceBlock
              evidence={message?.evidence}
              userQuestion={message?.userQuestion}
              answerText={text}
            />
            {!hasStructuredTable && null}
            {(message?.status || message?.confidence) && (
              <div className="chat-meta">
                {message.status && <span>status: {message.status}</span>}
                {message.confidence && (
                  <span>confidence: {message.confidence}</span>
                )}
              </div>
            )}
            {message?.showFeedback && (
              <FeedbackBar
                feedback={message.feedback}
                onThumbsUp={onThumbsUp}
                onThumbsDown={onThumbsDown}
                disabled={feedbackDisabled}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ChatMessage;
