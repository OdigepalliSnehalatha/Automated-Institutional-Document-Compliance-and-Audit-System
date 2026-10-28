import React, { useState } from "react";
import StatusBadge from "./StatusBadge";

function ComparisonModal({ isOpen, onClose, data, canDownload, onDownload }) {
  const [filter, setFilter] = useState("ALL"); // ALL | PASS | FAIL
  const [searchQuery, setSearchQuery] = useState("");

  if (!isOpen || !data) return null;

  const { file_name, document_type, final_result, comparison, analyzed_at } = data;
  const requirements = comparison?.requirements || [];
  const isAccepted = final_result === "ACCEPTED";

  const totalReqs = requirements.length;
  const passedReqs = requirements.filter((r) => r.status === "PASS").length;
  const failedReqs = requirements.filter((r) => r.status === "FAIL").length;
  const score = totalReqs > 0 ? Math.round((passedReqs / totalReqs) * 100) : 0;

  const filteredRequirements = requirements.filter((req) => {
    if (filter === "PASS" && req.status !== "PASS") return false;
    if (filter === "FAIL" && req.status !== "FAIL") return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = (req.name || "").toLowerCase().includes(q);
      const matchReason = (req.reason || "").toLowerCase().includes(q);
      const matchType = (req.type || "").toLowerCase().includes(q);
      if (!matchName && !matchReason && !matchType) return false;
    }
    return true;
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-dialog"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "850px", width: "95%" }}
      >
        <div className="modal-header">
          <div>
            <h3 style={{ fontSize: "17px", fontWeight: "800", color: "#0f172a" }}>
              Detailed Structural Comparison & Compliance Audit
            </h3>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
              Document: <strong>{file_name}</strong> {document_type && `• Type: ${document_type}`}
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: "75vh", overflowY: "auto" }}>
          {/* Strict Decision Banner */}
          <div className={`decision-banner ${final_result}`} style={{ marginBottom: "16px" }}>
            <div>
              <div className="decision-title">
                {isAccepted ? "✓ STRICT DECISION: ACCEPTED" : "✗ STRICT DECISION: REJECTED"}
              </div>
              <p style={{ fontSize: "13px", marginTop: "4px" }}>
                {isAccepted
                  ? "Every mandatory structural requirement, header, section, and format pattern passed verification."
                  : "One or more mandatory structural requirements failed verification. Under strict Boolean compliance, all rules must pass."}
              </p>
            </div>
            <div style={{ textAlign: "right" }}>
              <StatusBadge status={final_result} />
              <div style={{ fontSize: "18px", fontWeight: "900", marginTop: "4px", color: isAccepted ? "#059669" : "#dc2626" }}>
                {score}% Score
              </div>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", marginBottom: "16px" }}>
            <div style={{ background: "#f8fafc", padding: "10px 14px", borderRadius: "6px", border: "1px solid var(--border-color)", textAlign: "center" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "600" }}>Total Rules Checked</span>
              <div style={{ fontSize: "18px", fontWeight: "800", color: "#0f172a" }}>{totalReqs}</div>
            </div>
            <div style={{ background: "#f0fdf4", padding: "10px 14px", borderRadius: "6px", border: "1px solid #bbf7d0", textAlign: "center" }}>
              <span style={{ fontSize: "11px", color: "#166534", fontWeight: "600" }}>Mandatory Passed</span>
              <div style={{ fontSize: "18px", fontWeight: "800", color: "#15803d" }}>{passedReqs}</div>
            </div>
            <div style={{ background: "#fef2f2", padding: "10px 14px", borderRadius: "6px", border: "1px solid #fecaca", textAlign: "center" }}>
              <span style={{ fontSize: "11px", color: "#991b1b", fontWeight: "600" }}>Mandatory Failed</span>
              <div style={{ fontSize: "18px", fontWeight: "800", color: "#b91c1c" }}>{failedReqs}</div>
            </div>
          </div>

          {/* Controls: Search and Filters */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", marginBottom: "14px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#334155", margin: 0 }}>
              Comparison Matrix ({filteredRequirements.length} of {totalReqs})
            </h4>

            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <input
                type="text"
                placeholder="Filter by name or reason..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="form-input"
                style={{ width: "190px", padding: "4px 8px", fontSize: "12px" }}
              />

              <div style={{ display: "flex", gap: "2px", background: "#f1f5f9", padding: "2px", borderRadius: "4px" }}>
                <button
                  type="button"
                  onClick={() => setFilter("ALL")}
                  className={`btn btn-sm ${filter === "ALL" ? "btn-primary" : "btn-secondary"}`}
                  style={{ padding: "3px 8px", fontSize: "11px" }}
                >
                  All ({totalReqs})
                </button>
                <button
                  type="button"
                  onClick={() => setFilter("PASS")}
                  className={`btn btn-sm ${filter === "PASS" ? "btn-success" : "btn-secondary"}`}
                  style={{ padding: "3px 8px", fontSize: "11px" }}
                >
                  Passed ({passedReqs})
                </button>
                <button
                  type="button"
                  onClick={() => setFilter("FAIL")}
                  className={`btn btn-sm ${filter === "FAIL" ? "btn-danger" : "btn-secondary"}`}
                  style={{ padding: "3px 8px", fontSize: "11px" }}
                >
                  Failed ({failedReqs})
                </button>
              </div>
            </div>
          </div>

          {/* Detailed Requirements Checklist */}
          {filteredRequirements.length === 0 ? (
            <p className="empty-state">No requirement breakdown matches the selected filter.</p>
          ) : (
            <ul className="req-checklist">
              {filteredRequirements.map((req, idx) => (
                <li key={idx} className={`req-item ${req.status}`}>
                  <div className="req-icon">
                    {req.status === "PASS" ? "✓" : "✗"}
                  </div>
                  <div className="req-content">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <span className="req-name">{req.name}</span>
                        {req.type && (
                          <span
                            style={{
                              marginLeft: "8px",
                              fontSize: "10px",
                              fontWeight: "700",
                              padding: "2px 6px",
                              background: "#e2e8f0",
                              borderRadius: "4px",
                              color: "#475569",
                              textTransform: "uppercase",
                            }}
                          >
                            {req.type}
                          </span>
                        )}
                      </div>
                      <StatusBadge status={req.status} />
                    </div>

                    {req.status === "PASS" ? (
                      <div style={{ fontSize: "12px", color: "#16a34a", marginTop: "3px" }}>
                        ✓ Verified compliant against institutional blueprint.
                      </div>
                    ) : (
                      <div className="req-reason">
                        Reason: {req.reason || "Missing mandatory structural pattern."}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}

          {analyzed_at && (
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "16px", textAlign: "right" }}>
              Audit evaluation timestamp: {new Date(analyzed_at).toLocaleString()}
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
