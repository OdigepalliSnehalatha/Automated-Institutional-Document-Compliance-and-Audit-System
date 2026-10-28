import React, { useState, useEffect } from "react";
import api from "../api";

function ValidationReportModal({ isOpen, onClose, documentId, fileName, onViewPdf }) {
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterResult, setFilterResult] = useState("ALL");

  useEffect(() => {
    if (!isOpen || !documentId) {
      setReportData(null);
      return;
    }

    setLoading(true);
    setError(null);

    api.get(`/question-papers/${documentId}/report`)
      .then((res) => {
        setReportData(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setLoading(false);
        setError(err.response?.data?.detail || "Failed to load validation report.");
      });
  }, [isOpen, documentId]);

  if (!isOpen) return null;

  const report = reportData?.report || {};
  const summary = report.summary || {
    total_checks: 0,
    passed_checks: 0,
    failed_checks: 0,
    missing_requirements: 0,
    needs_review: 0,
    compliance_percentage: 0,
    validation_status: "PENDING"
  };
  const items = report.items || [];

  const filteredItems = items.filter((item) => {
    if (filterResult === "ALL") return true;
    if (filterResult === "CORRECT") return item.result === "Correct";
    if (filterResult === "FAILED") return item.result === "Incorrect" || item.result === "Missing";
    if (filterResult === "REVIEW") return item.result === "Needs Review";
    return true;
  });

  const getResultBadge = (result) => {
    switch (result) {
      case "Correct":
        return <span className="badge badge-success" style={{ fontWeight: 600 }}>✓ Correct</span>;
      case "Incorrect":
        return <span className="badge badge-danger" style={{ fontWeight: 600 }}>✕ Incorrect</span>;
      case "Missing":
        return <span className="badge badge-warning" style={{ fontWeight: 600, backgroundColor: "#d97706", color: "#fff" }}>⚠ Missing</span>;
      case "Needs Review":
        return <span className="badge badge-warning" style={{ fontWeight: 600, backgroundColor: "#8b5cf6", color: "#fff" }}>🔍 Needs Review</span>;
      case "Not Applicable":
        return <span className="badge badge-neutral" style={{ fontWeight: 500 }}>N/A</span>;
      default:
        return <span className="badge badge-neutral">{result || "Unknown"}</span>;
    }
  };

  const getApprovalBadge = (status) => {
    switch ((status || "").toUpperCase()) {
      case "ACCEPTED":
        return <span className="badge badge-success" style={{ padding: "4px 10px", fontSize: "13px" }}>✓ Formally Accepted</span>;
      case "REJECTED":
        return <span className="badge badge-danger" style={{ padding: "4px 10px", fontSize: "13px" }}>✕ Rejected</span>;
      case "NEEDS_REVIEW":
        return <span className="badge badge-warning" style={{ padding: "4px 10px", fontSize: "13px", backgroundColor: "#8b5cf6", color: "#fff" }}>🔍 Needs Review</span>;
      default:
        return <span className="badge badge-neutral" style={{ padding: "4px 10px", fontSize: "13px" }}>⏳ Pending Institutional Sign-off</span>;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" style={{ maxWidth: "1150px", maxHeight: "90vh", display: "flex", flexDirection: "column" }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header" style={{ borderBottom: "1px solid var(--border-color)", padding: "16px 24px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h3 style={{ margin: 0, fontSize: "18px" }}>Automated Document Validation Report</h3>
              {reportData && (
                <span className="badge" style={{ backgroundColor: "rgba(59, 130, 246, 0.15)", color: "#3b82f6", border: "1px solid rgba(59, 130, 246, 0.3)" }}>
                  Version {reportData.version}
                </span>
              )}
            </div>
            <p style={{ margin: "4px 0 0", fontSize: "13px", color: "var(--text-muted)" }}>
              {reportData?.course_code ? `${reportData.course_code} - ${reportData.course_name} | ` : ""}
              {fileName || reportData?.file_name} ({reportData?.exam_category || "Question Paper"})
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Body */}
        <div className="modal-body" style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          {loading && (
            <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
              <div className="spinner" style={{ width: "32px", height: "32px", margin: "0 auto 12px" }}></div>
              <p>Extracting and analyzing PDF document structure...</p>
            </div>
          )}

          {error && (
            <div className="alert alert-danger" style={{ marginBottom: "16px" }}>
              <strong>Error:</strong> {error}
            </div>
          )}

          {!loading && !error && reportData && (
            <>
              {/* Institutional Validation vs Approval Banner */}
              <div style={{
                background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
                border: "1px solid var(--border-color)",
                borderRadius: "8px",
                padding: "16px",
                marginBottom: "20px",
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "16px"
              }}>
                <div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    Automated System Validation
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "6px" }}>
                    <span style={{
                      fontSize: "20px",
                      fontWeight: 700,
                      color: summary.validation_status === "VALID" ? "#22c55e" : summary.validation_status === "INVALID" ? "#ef4444" : "#f59e0b"
                    }}>
                      {summary.validation_status}
                    </span>
                    <span style={{ fontSize: "14px", color: "var(--text-muted)" }}>
                      ({summary.compliance_percentage}% Compliance)
                    </span>
                  </div>
                  <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: "4px 0 0" }}>
                    Validated against institutional schema and examination standards.
                  </p>
                </div>

                <div style={{ borderLeft: "1px solid var(--border-color)", paddingLeft: "16px" }}>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    Institutional Human Approval
                  </div>
                  <div style={{ marginTop: "6px" }}>
                    {getApprovalBadge(reportData.approval_status)}
                  </div>
                  <p style={{ fontSize: "12px", color: "var(--text-muted)", margin: "4px 0 0" }}>
                    {reportData.approver_name ? (
                      <>Reviewed by <strong>{reportData.approver_name}</strong> on {reportData.approved_at}. {reportData.approval_comments && `"${reportData.approval_comments}"`}</>
                    ) : (
                      "Awaiting formal audit/HOD verification sign-off. Passing automated validation does not bypass approval."
                    )}
                  </p>
                </div>
              </div>

              {/* Summary Cards */}
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                gap: "12px",
                marginBottom: "20px"
              }}>
                <div className="card" style={{ padding: "12px 14px", textAlign: "center", background: "var(--surface)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Total Checks</div>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: "var(--text-main)", marginTop: "4px" }}>
                    {summary.total_checks}
                  </div>
                </div>

                <div className="card" style={{ padding: "12px 14px", textAlign: "center", background: "rgba(34, 197, 94, 0.08)", borderColor: "rgba(34, 197, 94, 0.3)" }}>
                  <div style={{ fontSize: "11px", color: "#22c55e", textTransform: "uppercase", fontWeight: 600 }}>Passed</div>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: "#22c55e", marginTop: "4px" }}>
                    {summary.passed_checks}
                  </div>
                </div>

                <div className="card" style={{ padding: "12px 14px", textAlign: "center", background: "rgba(239, 68, 68, 0.08)", borderColor: "rgba(239, 68, 68, 0.3)" }}>
                  <div style={{ fontSize: "11px", color: "#ef4444", textTransform: "uppercase", fontWeight: 600 }}>Failed</div>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: "#ef4444", marginTop: "4px" }}>
                    {summary.failed_checks}
                  </div>
                </div>

                <div className="card" style={{ padding: "12px 14px", textAlign: "center", background: "rgba(217, 119, 6, 0.08)", borderColor: "rgba(217, 119, 6, 0.3)" }}>
                  <div style={{ fontSize: "11px", color: "#d97706", textTransform: "uppercase", fontWeight: 600 }}>Missing</div>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: "#d97706", marginTop: "4px" }}>
                    {summary.missing_requirements}
                  </div>
                </div>

                <div className="card" style={{ padding: "12px 14px", textAlign: "center", background: "rgba(139, 92, 246, 0.08)", borderColor: "rgba(139, 92, 246, 0.3)" }}>
                  <div style={{ fontSize: "11px", color: "#8b5cf6", textTransform: "uppercase", fontWeight: 600 }}>Needs Review</div>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: "#8b5cf6", marginTop: "4px" }}>
                    {summary.needs_review}
                  </div>
                </div>

                <div className="card" style={{ padding: "12px 14px", textAlign: "center", background: "rgba(59, 130, 246, 0.08)", borderColor: "rgba(59, 130, 246, 0.3)" }}>
                  <div style={{ fontSize: "11px", color: "#3b82f6", textTransform: "uppercase", fontWeight: 600 }}>Compliance</div>
                  <div style={{ fontSize: "22px", fontWeight: 700, color: "#3b82f6", marginTop: "4px" }}>
                    {summary.compliance_percentage}%
                  </div>
                </div>
              </div>

              {/* Filter Tabs */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button
                    className={`btn btn-sm ${filterResult === "ALL" ? "btn-primary" : "btn-secondary"}`}
                    onClick={() => setFilterResult("ALL")}
                  >
                    All Results ({items.length})
                  </button>
                  <button
                    className={`btn btn-sm ${filterResult === "FAILED" ? "btn-primary" : "btn-secondary"}`}
                    onClick={() => setFilterResult("FAILED")}
                  >
                    Failed & Missing ({summary.failed_checks + summary.missing_requirements})
                  </button>
                  <button
                    className={`btn btn-sm ${filterResult === "REVIEW" ? "btn-primary" : "btn-secondary"}`}
                    onClick={() => setFilterResult("REVIEW")}
                  >
                    Needs Review ({summary.needs_review})
                  </button>
                  <button
                    className={`btn btn-sm ${filterResult === "CORRECT" ? "btn-primary" : "btn-secondary"}`}
                    onClick={() => setFilterResult("CORRECT")}
                  >
                    Passed ({summary.passed_checks})
                  </button>
                </div>

                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Showing {filteredItems.length} of {items.length} checks
                </span>
              </div>

              {/* Exact 6-Column Validation Results Table */}
              <div className="table-responsive" style={{ border: "1px solid var(--border-color)", borderRadius: "8px" }}>
                <table className="table" style={{ margin: 0, fontSize: "13px" }}>
                  <thead style={{ background: "rgba(30, 41, 59, 0.6)" }}>
                    <tr>
                      <th style={{ width: "16%", padding: "10px 12px" }}>Requirement</th>
                      <th style={{ width: "16%", padding: "10px 12px" }}>Expected Value / Rule</th>
                      <th style={{ width: "16%", padding: "10px 12px" }}>Detected Value</th>
                      <th style={{ width: "12%", padding: "10px 12px" }}>Result</th>
                      <th style={{ width: "20%", padding: "10px 12px" }}>Explanation</th>
                      <th style={{ width: "20%", padding: "10px 12px" }}>Recommended Correction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredItems.length === 0 ? (
                      <tr>
                        <td colSpan="6" style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)" }}>
                          No validation items match the selected filter.
                        </td>
                      </tr>
                    ) : (
                      filteredItems.map((item, idx) => {
                        const isFail = item.result === "Incorrect" || item.result === "Missing";
                        return (
                          <tr
                            key={idx}
                            style={{
                              backgroundColor: isFail ? "rgba(239, 68, 68, 0.04)" : item.result === "Needs Review" ? "rgba(139, 92, 246, 0.04)" : "transparent"
                            }}
                          >
                            <td style={{ padding: "10px 12px", fontWeight: 600, color: "var(--text-main)" }}>
                              {item.requirement}
                            </td>
                            <td style={{ padding: "10px 12px", color: "#93c5fd", fontFamily: "monospace", fontSize: "12px" }}>
                              {item.expected_value}
                            </td>
                            <td style={{ padding: "10px 12px", color: isFail ? "#fca5a5" : "#86efac", fontFamily: "monospace", fontSize: "12px" }}>
                              {item.detected_value}
                            </td>
                            <td style={{ padding: "10px 12px" }}>
                              {getResultBadge(item.result)}
                            </td>
                            <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontSize: "12px" }}>
                              {item.explanation}
                            </td>
                            <td style={{ padding: "10px 12px", color: isFail ? "#f59e0b" : "var(--text-muted)", fontSize: "12px", fontStyle: isFail ? "normal" : "italic" }}>
                              {item.recommended_correction || "—"}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer" style={{ borderTop: "1px solid var(--border-color)", padding: "14px 24px", display: "flex", justifyContent: "space-between" }}>
          <div>
            {onViewPdf && documentId && (
              <button
                className="btn btn-secondary"
                onClick={() => {
                  onClose();
                  onViewPdf(documentId, fileName);
                }}
              >
                📄 View Original PDF
              </button>
            )}
          </div>
          <button className="btn btn-primary" onClick={onClose}>
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
}

export default ValidationReportModal;
