import { NavLink, useNavigate } from "react-router-dom";
import TbxLogo from "./TbxLogo";

function NavIcon({ name }) {
  const common = {
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.75,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": true,
  };

  if (name === "chat") {
    return (
      <svg {...common}>
        <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z" />
      </svg>
    );
  }
  if (name === "dashboard") {
    return (
      <svg {...common}>
        <rect x="3" y="3" width="7" height="9" rx="1.5" />
        <rect x="14" y="3" width="7" height="5" rx="1.5" />
        <rect x="14" y="12" width="7" height="9" rx="1.5" />
        <rect x="3" y="16" width="7" height="5" rx="1.5" />
      </svg>
    );
  }
  if (name === "banks") {
    return (
      <svg {...common}>
        <path d="M3 10h18L12 3 3 10z" />
        <path d="M5 10v8M9.5 10v8M14.5 10v8M19 10v8" />
        <path d="M3 18h18" />
      </svg>
    );
  }
  if (name === "accounts") {
    return (
      <svg {...common}>
        <rect x="3" y="6" width="18" height="12" rx="2" />
        <path d="M3 10h18" />
        <circle cx="16" cy="14" r="1.25" fill="currentColor" stroke="none" />
      </svg>
    );
  }
  if (name === "transactions") {
    return (
      <svg {...common}>
        <path d="M7 7h12l-3-3M17 17H5l3 3" />
        <path d="M5 7v2a4 4 0 0 0 4 4h2M19 17v-2a4 4 0 0 0-4-4h-2" />
      </svg>
    );
  }
  return null;
}

function Sidebar({ collapsed, onToggle }) {
  const navigate = useNavigate();

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-top">
        <button
          className="menu-button"
          onClick={onToggle}
          type="button"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
          </svg>
        </button>

        {!collapsed && (
          <div className="brand-block">
            <TbxLogo size={30} showWordmark compact variant="on-dark" />
          </div>
        )}
      </div>

      {collapsed && (
        <div className="collapsed-brand" aria-hidden="true">
          <TbxLogo size={32} />
        </div>
      )}

      <button
        className="new-chat-button"
        type="button"
        onClick={() => navigate("/chat", { state: { reset: Date.now() } })}
      >
        <span className="new-chat-icon" aria-hidden="true">
          +
        </span>
        {!collapsed && <span>New conversation</span>}
      </button>

      <nav className="navigation" aria-label="Primary">
        <NavLink to="/chat" className="nav-item">
          <NavIcon name="chat" />
          {!collapsed && <span>TBX Insight</span>}
        </NavLink>

        <NavLink to="/dashboard" className="nav-item">
          <NavIcon name="dashboard" />
          {!collapsed && <span>Dashboard</span>}
        </NavLink>

        <NavLink to="/banks" className="nav-item">
          <NavIcon name="banks" />
          {!collapsed && <span>Banks</span>}
        </NavLink>

        <NavLink to="/accounts" className="nav-item">
          <NavIcon name="accounts" />
          {!collapsed && <span>Accounts</span>}
        </NavLink>

        <NavLink to="/transactions" className="nav-item">
          <NavIcon name="transactions" />
          {!collapsed && <span>Transactions</span>}
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <div className="bottom-item sidebar-status">
          <span className="status-dot" aria-hidden="true" />
          {!collapsed && (
            <span className="sidebar-status-text">
              <strong>TBX Finance</strong>
              <em>Demo workspace</em>
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
