import React from "react";

function Navbar({ user, onLogout }) {
  if (!user) return null;

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon">🏛️</div>
        <div>
          <h2>Automated Document Compliance System</h2>
          <p>{user.institution_name || user.institution || "Institutional Compliance"}</p>
        </div>
      </div>

      <div className="navbar-user">
        <div className="user-badge">
          <div className="user-name">
            {user.name || user.email}
            <span className={`role-tag role-${user.role}`}>{user.role}</span>
          </div>
          <div className="user-meta">
            {user.department_name ? `Dept: ${user.department_name}` : "Institutional Officer"}
          </div>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={onLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}

export default Navbar;
