import React from "react";

function Navbar({ user, onRequestLogout }) {
  if (!user) return null;

  // Extract initials for avatar
  const getInitials = (name, email) => {
    if (name) {
      const parts = name.trim().split(" ");
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    return email ? email.slice(0, 2).toUpperCase() : "U";
  };

  const initials = getInitials(user.name, user.email);

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon">🏛️</div>
        <div>
          <h2>Institutional Document Compliance System</h2>
          <p>
            <span className="status-dot"></span>
            {user.institution_name || user.institution || "Institutional Audit"}
          </p>
        </div>
      </div>

      <div className="navbar-user-section">
        <div className="user-profile-card">
          <div className="user-avatar">{initials}</div>
          <div className="user-details">
            <div className="user-name">
              <span>{user.name || user.email}</span>
              <span className={`role-tag role-${user.role}`}>{user.role}</span>
            </div>
            <div className="user-dept">
              {user.department_name ? `Dept: ${user.department_name}` : "All Departments / Institutional Scope"}
            </div>
          </div>
        </div>

        <button className="btn-signout" onClick={onRequestLogout} title="End session">
          <span>🚪</span>
          <span>Sign Out</span>
        </button>
      </div>
    </header>
  );
}

export default Navbar;
