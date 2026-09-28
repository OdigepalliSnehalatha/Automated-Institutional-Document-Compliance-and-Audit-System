import React from "react";
import StatusBadge from "./StatusBadge";

function ComparisonModal({ isOpen, onClose, data, canDownload, onDownload }) {
  if (!isOpen || !data) return null;

  const { file_name, document_type, final_result, comparison, analyzed_at } = data;
  const requirements = comparison?.requirements || [];
  const isAccepted = final_result === "ACCEPTED";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Structural Comparison Results</h3>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
              Document: <strong>{file_name}</strong> {document_type && `(${document_type})`}
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          {/* Strict Decision Banner */}
          <div className={`decision-banner ${final_result}`}>
            <div>
              <div className="decision-title">
                {isAccepted ? "✓ FINAL DECISION: ACCEPTED" : "✗ FINAL DECISION: REJECTED"}
              </div>
              <p style={{ fontSize: "13px", marginTop: "4px" }}>
                {isAccepted
                  ? "Every required structural requirement passed verification."
                  : "One or more mandatory structural requirements failed. Documents must strictly satisfy all structural requirements."}
              </p>
            </div>
            <StatusBadge status={final_result} />
          </div>

          <h4 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "12px", color: "#334155" }}>
            Structural Requirements Checklist ({requirements.length})
          </h4>

          {requirements.length === 0 ? (
            <p className="empty-state">No requirement breakdown available.</p>
          ) : (
            <ul className="req-checklist">
              {requirements.map((req, idx) => (
                <li key={idx} className={`req-item ${req.status}`}>
                  <div className="req-icon">
                    {req.status === "PASS" ? "✓" : "✗"}
                  </div>
                  <div className="req-content">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span className="req-name">{req.name}</span>
                      <StatusBadge status={req.status} />
                    </div>
                    {req.status === "FAIL" && req.reason && (
                      <div className="req-reason">
                        Reason: {req.reason}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}

          {analyzed_at && (
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "16px", textAlign: "right" }}>
              Analyzed at: {new Date(analyzed_at).toLocaleString()}
            </p>
          )}
        </div>

        <div className="modal-footer">
          {isAccepted && canDownload && (
            <button className="btn btn-success" onClick={() => onDownload(data.document_id, file_name)}>
              📥 Download Accepted PDF
            </button>
          )}
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default ComparisonModal;
