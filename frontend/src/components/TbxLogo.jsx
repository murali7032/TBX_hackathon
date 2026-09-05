/** Official-style TBX mark: shield-in-t + wordmark with cyan growth stroke on X. */
function TbxLogo({
  size = 36,
  showWordmark = false,
  compact = false,
  variant = "light",
  className = "",
}) {
  const navy = "#0B1F3A";
  const cyan = "#00AEEF";
  const markFill = variant === "dark" ? "#E8F4FC" : "#FFFFFF";

  const mark = (
    <svg
      className="tbx-logo-mark"
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <circle cx="24" cy="24" r="23" fill={navy} />
      {/* stylized t */}
      <path
        d="M15 15.5h18M24.5 15.5v21c0 1.2-.9 2.2-2.1 2.2h-.8c-1.2 0-2.1-1-2.1-2.2V24"
        stroke={markFill}
        strokeWidth="3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* cyan arc */}
      <path
        d="M34.5 14.5a14 14 0 0 1-1.4 19.2"
        stroke={cyan}
        strokeWidth="3"
        strokeLinecap="round"
      />
      {/* shield */}
      <path
        d="M21.6 19.2 24 17.6l2.4 1.6v2.8L24 23.6l-2.4-1.6v-2.8z"
        fill={cyan}
      />
    </svg>
  );

  if (!showWordmark) {
    return <span className={`tbx-logo ${className}`}>{mark}</span>;
  }

  const textColor = variant === "on-dark" ? "#F4F8FC" : navy;

  return (
    <span className={`tbx-logo tbx-logo-with-wordmark ${className}`}>
      {mark}
      <span className="tbx-wordmark">
        <span className="tbx-wordmark-primary" style={{ color: textColor }}>
          TB
          <span className="tbx-x">
            <span className="tbx-x-navy">X</span>
            <span className="tbx-x-cyan" aria-hidden="true">
              X
            </span>
          </span>
          {!compact && <span className="tbx-wordmark-finance"> Finance</span>}
        </span>
        {compact && <span className="tbx-wordmark-secondary">Workspace</span>}
        {!compact && <span className="tbx-wordmark-secondary">Insight</span>}
      </span>
    </span>
  );
}

export default TbxLogo;
