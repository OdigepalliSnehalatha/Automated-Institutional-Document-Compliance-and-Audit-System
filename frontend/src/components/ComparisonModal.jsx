import React, { useState } from "react";
import StatusBadge from "./StatusBadge";

function ComparisonModal({ isOpen, onClose, data, canDownload, onDownload }) {
  const [activeCategory, setActiveCategory] = useState("ALL"); // ALL | CORRECT | INCORRECT | MISSING
  const [searchQuery, setSearchQuery] = useState("");

  if (!isOpen || !data) return null;

  const { file_name, document_type, final_result, comparison, analyzed_at } = data;
  
  // Extract items from comparison result
  const rawItems = comparison?.items || [];
  const items = rawItems.length > 0 ? rawItems : (comparison?.requirements || []).map((r) => ({
    requirement: r.name,
    expected_value: r.type || "Mandatory Institutional Requirement",
    detected_value: r.detected || (r.status === "PASS" ? "Verified" : "Failed"),
    result: r.status === "PASS" ? "Correct" : "Incorrect",
    explanation: r.reason || (r.status === "PASS" ? "Verified compliant." : "Failed verification."),
    recommended_correction: r.correction || "Update document according to standard requirements."
  }));

  const correctReqs = comparison?.correct_requirements || items.filter((it) => it.result === "Correct");
  const incorrectReqs = comparison?.incorrect_requirements || items.filter((it) => it.result === "Incorrect");
  const missingReqs = comparison?.missing_requirements || items.filter((it) => it.result === "Missing");
  const reviewReqs = items.filter((it) => it.result === "Needs Review");

  const marksInfo = comparison?.marks_verification;

  const totalChecks = items.length;
  const passedChecks = correctReqs.length;
  const failedChecks = incorrectReqs.length;
  const missingCount = missingReqs.length;
  const reviewCount = reviewReqs.length;

  const compliancePct = totalChecks > 0 ? Math.round((passedChecks / totalChecks) * 100) : 0;
  const isAccepted = final_result === "ACCEPTED" || final_result === "VALID";
  const isPendingReview = final_result === "PENDING REVIEW" || final_result === "NEEDS_REVIEW";

  const displayedItems = items.filter((item) => {
    if (activeCategory === "CORRECT" && item.result !== "Correct") return false;
    if (activeCategory === "INCORRECT" && item.result !== "Incorrect") return false;
    if (activeCategory === "MISSING" && item.result !== "Missing") return false;
    if (activeCategory === "REVIEW" && item.result !== "Needs Review") return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchReq = (item.requirement || "").toLowerCase().includes(q);
      const matchExp = (item.expected_value || "").toLowerCase().includes(q);
      const matchDet = (item.detected_value || "").toLowerCase().includes(q);
      const matchExpl = (item.explanation || "").toLowerCase().includes(q);
      if (!matchReq && !matchExp && !matchDet && !matchExpl) return false;
    }
    return true;
  });

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-dialog"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: "980px", width: "95%", maxHeight: "90vh", display: "flex", flexDirection: "column" }}
      >
        {/* Header */}
        <div className="modal-header" style={{ padding: "18px 24px", borderBottom: "1px solid #e2e8f0" }}>
          <div>
            <h3 style={{ fontSize: "18px", fontWeight: "800", color: "#0f172a", margin: 0 }}>
              Institutional Document Compliance & Validation Report
            </h3>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: "4px 0 0" }}>
              Document: <strong>{file_name}</strong> {document_type && `• Category: ${document_type}`}
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} style={{ fontSize: "18px", cursor: "pointer" }}>
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body" style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {/* E. FINAL COMPLIANCE STATUS BANNER */}
          <div
            style={{
              padding: "16px 20px",
              borderRadius: "8px",
              marginBottom: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: isAccepted ? "#f0fdf4" : isPendingReview ? "#faf5ff" : "#fef2f2",
              border: `1px solid ${isAccepted ? "#86efac" : isPendingReview ? "#d8b4fe" : "#fca5a5"}`,
            }}
          >
            <div>
              <div style={{ fontSize: "16px", fontWeight: "800", color: isAccepted ? "#15803d" : isPendingReview ? "#6b21a8" : "#b91c1c" }}>
                {isAccepted
                  ? "✓ FINAL COMPLIANCE STATUS: ACCEPTED"
                  : isPendingReview
                  ? "🔍 FINAL COMPLIANCE STATUS: PENDING REVIEW"
                  : "✕ FINAL COMPLIANCE STATUS: REJECTED"}
              </div>
              <p style={{ fontSize: "13px", margin: "4px 0 0", color: "#334155" }}>
                {isAccepted
                  ? "All mandatory institutional requirements, sections, unit structures, and marks distributions are satisfied."
                  : isPendingReview
                  ? "Document text could not be extracted with high confidence (scanned or image-based). Requires manual Auditor review."
                  : "One or more mandatory requirements, unit structures, or marks allocations failed or are missing."}
              </p>
            </div>
            <div style={{ textAlign: "right", minWidth: "120px" }}>
              <StatusBadge status={isAccepted ? "ACCEPTED" : isPendingReview ? "NEEDS_REVIEW" : "REJECTED"} />
              <div style={{ fontSize: "18px", fontWeight: "800", marginTop: "6px", color: isAccepted ? "#15803d" : isPendingReview ? "#7e22ce" : "#dc2626" }}>
                {compliancePct}% Score
              </div>
            </div>
          </div>

          {/* D. MARKS VERIFICATION PANEL */}
          {marksInfo && (
            <div
              style={{
                background: "#f8fafc",
                padding: "14px 18px",
                borderRadius: "8px",
                border: "1px solid #e2e8f0",
                marginBottom: "16px",
                display: "grid",
                gridTemplateColumns: "1fr 1fr 2fr",
                gap: "12px",
                alignItems: "center"
              }}
            >
              <div>
                <span style={{ fontSize: "11px", fontWeight: "700", color: "#64748b", textTransform: "uppercase" }}>Expected Marks</span>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "#0f172a" }}>{marksInfo.expected_marks} Marks</div>
              </div>
              <div>
                <span style={{ fontSize: "11px", fontWeight: "700", color: "#64748b", textTransform: "uppercase" }}>Detected Marks</span>
                <div style={{ fontSize: "16px", fontWeight: "800", color: marksInfo.status === "Correct" ? "#15803d" : "#dc2626" }}>
                  {marksInfo.detected_marks} Marks
                </div>
              </div>
              <div>
                <span style={{ fontSize: "11px", fontWeight: "700", color: "#64748b", textTransform: "uppercase" }}>Marks Calculation Breakdown</span>
                <div style={{ fontSize: "12px", fontWeight: "600", color: "#334155" }}>
                  {marksInfo.calculation_breakdown || "N/A"}
                </div>
              </div>
            </div>
          )}

          {/* Category Tabs: A. Correct, B. Incorrect, C. Missing */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px", marginBottom: "14px" }}>
            <div style={{ display: "flex", gap: "6px", background: "#f1f5f9", padding: "4px", borderRadius: "6px" }}>
              <button
                type="button"
                onClick={() => setActiveCategory("ALL")}
                className={`btn btn-sm ${activeCategory === "ALL" ? "btn-primary" : "btn-secondary"}`}
                style={{ padding: "4px 10px", fontSize: "12px", fontWeight: 600 }}
              >
                All Rules ({totalChecks})
              </button>
              <button
                type="button"
                onClick={() => setActiveCategory("CORRECT")}
                className={`btn btn-sm ${activeCategory === "CORRECT" ? "btn-success" : "btn-secondary"}`}
                style={{ padding: "4px 10px", fontSize: "12px", fontWeight: 600, color: activeCategory === "CORRECT" ? "#fff" : "#166534" }}
              >
                ✓ A. Correct ({passedChecks})
              </button>
              <button
                type="button"
                onClick={() => setActiveCategory("INCORRECT")}
                className={`btn btn-sm ${activeCategory === "INCORRECT" ? "btn-danger" : "btn-secondary"}`}
                style={{ padding: "4px 10px", fontSize: "12px", fontWeight: 600, color: activeCategory === "INCORRECT" ? "#fff" : "#991b1b" }}
              >
                ✕ B. Incorrect ({failedChecks})
              </button>
              <button
                type="button"
                onClick={() => setActiveCategory("MISSING")}
                className={`btn btn-sm ${activeCategory === "MISSING" ? "btn-warning" : "btn-secondary"}`}
                style={{ padding: "4px 10px", fontSize: "12px", fontWeight: 600, color: activeCategory === "MISSING" ? "#fff" : "#b45309" }}
              >
                ⚠ C. Missing ({missingCount})
              </button>
              {reviewCount > 0 && (
                <button
                  type="button"
                  onClick={() => setActiveCategory("REVIEW")}
                  className={`btn btn-sm btn-secondary`}
                  style={{ padding: "4px 10px", fontSize: "12px", fontWeight: 600, color: "#6b21a8" }}
                >
                  🔍 Review ({reviewCount})
                </button>
              )}
            </div>

            <input
              type="text"
              placeholder="Search requirements..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input"
              style={{ width: "210px", padding: "5px 10px", fontSize: "12px" }}
            />
          </div>

          {/* Tabular Validation Breakdown List */}
          {displayedItems.length === 0 ? (
            <p className="empty-state" style={{ textAlign: "center", padding: "30px", color: "var(--text-muted)" }}>
              No requirements found matching the selected filter.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {displayedItems.map((item, idx) => {
                const isItemCorrect = item.result === "Correct";
                const isItemMissing = item.result === "Missing";
                const isItemReview = item.result === "Needs Review";

                const badgeBg = isItemCorrect ? "#dcfce7" : isItemMissing ? "#fef3c7" : isItemReview ? "#f3e8ff" : "#fee2e2";
                const badgeColor = isItemCorrect ? "#15803d" : isItemMissing ? "#b45309" : isItemReview ? "#6b21a8" : "#b91c1c";
                const badgeBorder = isItemCorrect ? "#86efac" : isItemMissing ? "#fde68a" : isItemReview ? "#d8b4fe" : "#fca5a5";

                return (
                  <div
                    key={idx}
                    style={{
                      background: "#ffffff",
                      border: `1px solid ${isItemCorrect ? "#e2e8f0" : badgeBorder}`,
                      borderRadius: "8px",
                      padding: "14px 16px",
                      boxShadow: "0 1px 2px rgba(0,0,0,0.03)"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                      <div style={{ fontWeight: 700, fontSize: "14px", color: "#0f172a" }}>
                        {item.requirement}
                      </div>
                      <span
                        style={{
                          fontSize: "11px",
                          fontWeight: 700,
                          padding: "3px 8px",
                          borderRadius: "4px",
                          background: badgeBg,
                          color: badgeColor,
                          border: `1px solid ${badgeBorder}`
                        }}
                      >
                        {item.result === "Correct" ? "✓ Correct" : item.result === "Missing" ? "⚠ Missing" : item.result === "Needs Review" ? "🔍 Needs Review" : "✕ Incorrect"}
                      </span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "12px", marginBottom: "8px" }}>
                      <div>
                        <strong style={{ color: "#475569" }}>Expected: </strong>
                        <span style={{ color: "#0f172a" }}>{item.expected_value}</span>
                      </div>
                      <div>
                        <strong style={{ color: "#475569" }}>Detected: </strong>
                        <span style={{ color: isItemCorrect ? "#15803d" : "#b91c1c" }}>{item.detected_value}</span>
                      </div>
                    </div>

                    <div style={{ fontSize: "12px", color: "#334155", background: "#f8fafc", padding: "8px 12px", borderRadius: "6px", border: "1px solid #f1f5f9" }}>
                      <strong>Audit Explanation: </strong> {item.explanation}
                      {item.recommended_correction && item.recommended_correction !== "None required." && (
                        <div style={{ marginTop: "4px", color: "#b45309" }}>
                          <strong>Recommended Correction: </strong> {item.recommended_correction}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {analyzed_at && (
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "16px", textAlign: "right" }}>
              Automated audit timestamp: {new Date(analyzed_at).toLocaleString()}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer" style={{ padding: "14px 24px", borderTop: "1px solid #e2e8f0", display: "flex", justifyContent: "flex-end", gap: "10px" }}>
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
