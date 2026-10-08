import React from "react";

function LogoutModal({ isOpen, onClose, onConfirm, user }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog modal-dialog-sm" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>🚪 Sign Out Confirmation</h3>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body" style={{ textAlign: "center", padding: "30px 24px" }}>
          <div style={{ fontSize: "40px", marginBottom: "14px" }}>🔒</div>
          <h4 style={{ fontSize: "16px", fontWeight: "700", color: "#0f172a", marginBottom: "8px" }}>
            Ready to end your session?
          </h4>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: "1.5" }}>
            You are logged in as <strong>{user?.name || user?.email}</strong> (<em>{user?.role}</em>).
            Signing out will securely terminate your authenticated server session.
          </p>
        </div>

        <div className="modal-footer" style={{ justifyContent: "center", gap: "12px" }}>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-danger" onClick={onConfirm}>
            Yes, Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

export default LogoutModal;
