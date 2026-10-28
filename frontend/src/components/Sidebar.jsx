import React from "react";
import InstitutionLogo from "./InstitutionLogo";

function Sidebar({
  user,
  activeTab,
  onSelectTab,
  onRequestLogout,
  onOpenAiChat,
  counts = {},
  mobileOpen = false,
  onCloseMobile = () => {},
}) {
  if (!user) return null;

  // Role metadata definitions
  const roleConfig = {
    Admin: {
      portalTitle: "Admin Workspace",
      roleBadgeClass: "role-Admin",
      navItems: [
        { id: "overview", label: "Dashboard Overview", icon: "🏠" },
        { id: "question_papers", label: "Question Papers", icon: "📝" },
        { id: "institution", label: "Institution & Logo", icon: "🏫" },
        { id: "personnel", label: "Faculty & Staff", icon: "👥", badge: counts.total_personnel },
        { id: "departments", label: "Departments & Branches", icon: "🏢", badge: counts.total_departments },
        { id: "documents", label: "Audit Documents", icon: "📁", badge: counts.total_documents },
      ],
    },
    Auditor: {
      portalTitle: "Auditor Workspace",
      roleBadgeClass: "role-Auditor",
      navItems: [
        { id: "overview", label: "Overview & Analytics", icon: "📊" },
        { id: "question_papers", label: "Question Papers", icon: "📝" },
        { id: "builder", label: "Format Builder", icon: "⚙️" },
        { id: "formats", label: "Master Formats", icon: "📑", badge: counts.total_formats },
        { id: "submissions", label: "All Submissions", icon: "📁", badge: counts.total_submissions },
        { id: "accepted", label: "Accepted Official PDFs", icon: "✓", badge: counts.accepted_documents },
      ],
    },
    HOD: {
      portalTitle: `${user.department_name || "Department"} HOD`,
      roleBadgeClass: "role-HOD",
      navItems: [
        { id: "overview", label: "Department Overview", icon: "📊" },
        { id: "question_papers", label: "Question Papers", icon: "📝" },
        { id: "all", label: "Faculty Submissions", icon: "📁", badge: counts.department_documents },
        { id: "accepted", label: "Accepted Official PDFs", icon: "✓", badge: counts.accepted_documents },
        { id: "branches", label: "Branches & Guidelines", icon: "🏫" },
      ],
    },
    Faculty: {
      portalTitle: "Faculty Portal",
      roleBadgeClass: "role-Faculty",
      navItems: [
        { id: "question_papers", label: "Question Papers", icon: "📝" },
        { id: "upload", label: "Upload & Verify", icon: "📤" },
        { id: "submissions", label: "My Submissions", icon: "📁", badge: counts.my_documents },
        { id: "guidelines", label: "Compliance Rules", icon: "📋" },
      ],
    },
  };

  const currentRoleConfig = roleConfig[user.role] || roleConfig.Faculty;

  // Initials for avatar
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
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${mobileOpen ? "open" : ""}`}>
        {/* Sidebar Brand Header */}
        <div className="sidebar-header">
          <div className="sidebar-brand-wrapper">
            <InstitutionLogo logoUrl={user.institution_logo} size={36} />
            <div className="sidebar-brand-text">
              <h2 className="sidebar-brand-name">
                {user.institution_name || user.institution || "Compliance System"}
              </h2>
              <span className="sidebar-brand-sub">Academic Audit SaaS</span>
            </div>
          </div>
          {mobileOpen && (
            <button
              className="sidebar-close-btn"
              onClick={onCloseMobile}
              title="Close Menu"
            >
              ✕
            </button>
          )}
        </div>

        {/* Role Workspace Banner */}
        <div className="sidebar-role-banner">
          <span className="sidebar-role-label">PORTAL</span>
          <span className={`role-tag ${currentRoleConfig.roleBadgeClass}`}>
            {currentRoleConfig.portalTitle}
          </span>
        </div>

        {/* Navigation List */}
        <nav className="sidebar-nav">
          <div className="sidebar-nav-group-title">MAIN NAVIGATION</div>

          {currentRoleConfig.navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                onClick={() => {
                  onSelectTab(item.id);
                  onCloseMobile();
                }}
              >
                <span className="nav-item-icon">{item.icon}</span>
                <span className="nav-item-label">{item.label}</span>
                {item.badge !== undefined && item.badge !== null && item.badge !== 0 && (
                  <span className="nav-item-badge">{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer with User Profile and Sign Out */}
        <div className="sidebar-footer">
          <div className="sidebar-user-card">
            <div className="sidebar-avatar">
              {initials}
              <span className="online-indicator-dot" title="Active Session"></span>
            </div>
            <div className="sidebar-user-meta">
              <span className="sidebar-user-name" title={user.name || user.email}>
                {user.name || user.email}
              </span>
              <span className="sidebar-user-dept">
                {user.department_name ? user.department_name : user.role}
              </span>
            </div>
          </div>

          <button
            className="sidebar-signout-btn"
            onClick={onRequestLogout}
            title="Log out from your session"
          >
            <span className="signout-icon">🚪</span>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
