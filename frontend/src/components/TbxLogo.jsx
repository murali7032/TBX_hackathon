import logoMark from "../assets/tbx-logo.png";

/** TBX brand mark from official logo artwork + optional wordmark. */
function TbxLogo({
  size = 36,
  showWordmark = false,
  compact = false,
  variant = "light",
  className = "",
}) {
  const navy = "#0B1F3A";
  const textColor = variant === "on-dark" ? "#F4F8FC" : navy;

  const mark = (
    <img
      className="tbx-logo-mark"
      src={logoMark}
      alt=""
      width={size}
      height={size}
      style={{ width: size, height: size }}
      draggable={false}
    />
  );

  if (!showWordmark) {
    return (
      <span className={`tbx-logo ${className}`} aria-hidden="true">
        {mark}
      </span>
    );
  }

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
