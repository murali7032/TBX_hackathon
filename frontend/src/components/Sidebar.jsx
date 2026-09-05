import { NavLink, useNavigate } from "react-router-dom";

function Sidebar({ collapsed, onToggle }) {
  const navigate = useNavigate();

  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
      <div className="sidebar-top">
        <button className="menu-button" onClick={onToggle} type="button">
          ☰
        </button>

        {!collapsed && <span className="brand-name">TBX Finance</span>}
      </div>

      <button
        className="new-chat-button"
        type="button"
        onClick={() => navigate("/chat", { state: { reset: Date.now() } })}
      >
        <span>＋</span>
        {!collapsed && <span>New chat</span>}
      </button>

      <nav className="navigation">
        <NavLink to="/chat" className="nav-item">
          <span>◌</span>
          {!collapsed && <span>Chat</span>}
        </NavLink>

        <NavLink to="/dashboard" className="nav-item">
          <span>⌂</span>
          {!collapsed && <span>Dashboard</span>}
        </NavLink>

        <NavLink to="/banks" className="nav-item">
          <span>🏦</span>
          {!collapsed && <span>Banks</span>}
        </NavLink>

        <NavLink to="/accounts" className="nav-item">
          <span>◎</span>
          {!collapsed && <span>Accounts</span>}
        </NavLink>

        <NavLink to="/transactions" className="nav-item">
          <span>↕</span>
          {!collapsed && <span>Transactions</span>}
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <div className="bottom-item">
          <span>✦</span>
          {!collapsed && <span>Gemini</span>}
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
