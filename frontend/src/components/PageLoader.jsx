import TbxLogo from "./TbxLogo";

/**
 * Professional TBX-themed page loader.
 * variant: "block" (default full section) | "inline" | "overlay"
 */
function PageLoader({
  label = "Loading workspace data…",
  hint = "Fetching ledger records securely",
  variant = "block",
}) {
  return (
    <div
      className={`tbx-loader tbx-loader-${variant}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="tbx-loader-mark">
        <span className="tbx-loader-ring" aria-hidden="true" />
        <span className="tbx-loader-ring tbx-loader-ring-delay" aria-hidden="true" />
        <TbxLogo size={44} />
      </div>
      <div className="tbx-loader-copy">
        <p className="tbx-loader-label">{label}</p>
        {hint && <p className="tbx-loader-hint">{hint}</p>}
      </div>
      <div className="tbx-loader-bars" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

/** Skeleton shimmer for tables while data loads */
function TableSkeleton({ rows = 6, cols = 4 }) {
  return (
    <div className="tbx-skeleton-table" aria-hidden="true">
      <div className="tbx-skeleton-head">
        {Array.from({ length: cols }).map((_, i) => (
          <span key={`h-${i}`} className="tbx-skel" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div className="tbx-skeleton-row" key={`r-${r}`}>
          {Array.from({ length: cols }).map((_, c) => (
            <span
              key={`c-${r}-${c}`}
              className="tbx-skel"
              style={{ animationDelay: `${(r * cols + c) * 0.04}s` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export { TableSkeleton };
export default PageLoader;
