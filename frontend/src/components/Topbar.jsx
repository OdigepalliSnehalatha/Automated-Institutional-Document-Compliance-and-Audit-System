import React, { useState } from "react";
import InstitutionLogo from "./InstitutionLogo";

function Topbar({
  user,
  title,
  subtitle,
  onOpenMobileMenu,
  onOpenAiChat,
  notifications = [],
}) {
  const [showNotifications, setShowNotifications] = useState(false);

  const getInitials = (name, email) => {
    if (name) {
      const parts = name.trim().split(" ");
      if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
      return name.slice(0, 2).toUpperCase();
    }
    return email ? email.slice(0, 2).toUpperCase() : "U";
  };

  const initials = getInitials(user?.name, user?.email);

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="topbar-hamburger-btn"
          onClick={onOpenMobileMenu}
          title="Open Menu"
        >
          ☰
        </button>

        <div className="topbar-titles">
          <div className="topbar-breadcrumbs">
            <span>{user?.institution_name || "Institution"}</span>
            <span className="breadcrumb-sep">/</span>
            <span className="breadcrumb-active">{user?.role}</span>
          </div>
          <h1 className="topbar-page-title">{title || "Dashboard"}</h1>
          {subtitle && <p className="topbar-page-subtitle">{subtitle}</p>}
        </div>
      </div>

      <div className="topbar-right">
        {/* Operational Status Pill */}
        <div className="topbar-status-pill" title="Backend & Database Connected">
          <span className="status-live-dot"></span>
          <span>System Operational</span>
        </div>

        {/* Notifications Icon & Popover */}
        <div className="notifications-wrapper" style={{ position: "relative" }}>
          <button
            className="topbar-icon-btn"
            onClick={() => setShowNotifications(!showNotifications)}
            title="Notifications & Activity"
          >
            <span>🔔</span>
            {notifications.length > 0 && (
              <span className="notif-badge">{notifications.length}</span>
            )}
          </button>

          {showNotifications && (
            <div className="notifications-popover">
              <div className="notifications-header">
                <h4>System Notifications</h4>
                <button
                  className="notif-close-btn"
                  onClick={() => setShowNotifications(false)}
                >
                  ✕
                </button>
              </div>
              <div className="notifications-body">
                {notifications.length === 0 ? (
                  <p className="notif-empty">No unread notifications.</p>
                ) : (
                  notifications.map((n, idx) => (
                    <div key={idx} className="notif-item">
                      <div className="notif-icon">📄</div>
                      <div className="notif-text">
                        <p className="notif-title">{n.title || n.message}</p>
                        <span className="notif-time">{n.time || "Recent"}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* User Mini Profile Tag */}
        <div className="topbar-user-pill">
          <div className="topbar-avatar">{initials}</div>
          <div className="topbar-user-info">
            <span className="topbar-name">{user?.name || user?.email}</span>
            <span className={`role-tag role-${user?.role}`}>{user?.role}</span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Topbar;
