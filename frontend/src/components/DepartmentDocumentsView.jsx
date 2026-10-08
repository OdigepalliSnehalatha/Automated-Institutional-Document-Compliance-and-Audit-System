import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "./StatusBadge";
import ComparisonModal from "./ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function DepartmentDocumentsView({ department, onBack, user }) {
  const [documents, setDocuments] = useState([]);
  const [jntuaSubjects, setJntuaSubjects] = useState([]);
  const [deptInfo, setDeptInfo] = useState(department || {});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeSubTab, setActiveSubTab] = useState("subjects"); // "subjects" | "documents"

  // Search & Filter for Documents
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Search & Filter for Subjects
  const [subjectSearch, setSubjectSearch] = useState("");
  const [expandedUnitCode, setExpandedUnitCode] = useState(null);

  // Modals
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  useEffect(() => {
    loadDepartmentData();
  }, [department]);

  const loadDepartmentData = async () => {
    setLoading(true);
    setError("");
    try {
      let res;
      if (department?.id) {
        res = await api.get(`/documents/by-department/${department.id}`);
      } else if (department?.code) {
        res = await api.get(`/documents/by-department/code/${department.code}`);
      } else {
        res = await api.get("/documents");
      }
      setDocuments(res.data.documents || []);
      setJntuaSubjects(res.data.jntua_subjects || []);
      if (res.data.department) {
        setDeptInfo(res.data.department);
      }
    } catch (err) {
      console.error("Failed to load department data:", err);
      setError("Unable to load department data.");
    } finally {
      setLoading(false);
    }
  };

  const openComparisonModal = async (docId) => {
    try {
      const res = await api.get(`/documents/${docId}/comparison`);
      setComparisonData(res.data);
      setComparisonModalOpen(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Unable to load comparison results.");
    }
  };

  const handleDownload = (docId, fileName) => {
    window.open(`http://localhost:8000/documents/${docId}/download`, "_blank");
  };

  const totalCount = documents.length;
  const acceptedCount = documents.filter((d) => d.analysis_status === "ACCEPTED").length;
  const rejectedCount = documents.filter((d) => d.analysis_status === "REJECTED").length;
  const pendingCount = documents.filter((d) => !d.analysis_status || d.analysis_status === "PENDING").length;
  const complianceRate = totalCount > 0 ? Math.round((acceptedCount / totalCount) * 100) : 0;

  const filteredDocs = documents.filter((doc) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !q ||
      doc.file_name.toLowerCase().includes(q) ||
      (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
      (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q));
    const matchesStatus =
      statusFilter === "ALL" ||
      doc.analysis_status === statusFilter ||
      (statusFilter === "PENDING" && (!doc.analysis_status || doc.analysis_status === "PENDING"));
    return matchesSearch && matchesStatus;
  });

  const filteredSubjects = jntuaSubjects.filter((s) => {
    const q = subjectSearch.toLowerCase();
    return (
      !q ||
      s.name.toLowerCase().includes(q) ||
      s.code.toLowerCase().includes(q) ||
      s.semester.toLowerCase().includes(q)
    );
  });

  return (
    <div className="panel" style={{ animation: "fadeIn 0.25s ease-out" }}>
      {/* Top Breadcrumb & Back Navigation */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "18px", borderBottom: "1px solid var(--border-color)", paddingBottom: "14px" }}>
        <button
          className="btn btn-secondary btn-sm"
          onClick={onBack}
          style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700" }}
        >
          <span>← Back to Departments</span>
        </button>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className="branch-pill" style={{ fontSize: "13px", padding: "4px 12px" }}>
            {deptInfo.code || department?.code}
          </span>
          <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            JNTUA Affiliated • {user?.institution_name || "ALITS"}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="panel-header" style={{ marginBottom: "16px" }}>
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#0f172a", margin: "0 0 6px" }}>
            🏛️ {deptInfo.name || department?.name} ({deptInfo.code || department?.code})
          </h2>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: 0 }}>
            Official JNTUA Curriculum (R20/R23 Regulations) & Uploaded Compliance Audit Records
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadDepartmentData} disabled={loading}>
          ↻ Refresh
        </button>
      </div>

      {/* Sub-Tabs: JNTUA Subjects vs Uploaded Documents */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", borderBottom: "2px solid #e2e8f0" }}>
        <button
          type="button"
          onClick={() => setActiveSubTab("subjects")}
          style={{
            padding: "10px 18px",
            border: "none",
            background: "none",
            borderBottom: activeSubTab === "subjects" ? "3px solid #2563eb" : "3px solid transparent",
            color: activeSubTab === "subjects" ? "#2563eb" : "#64748b",
            fontWeight: "700",
            fontSize: "14px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>📚 JNTUA Syllabus & Subjects</span>
          <span style={{ background: activeSubTab === "subjects" ? "#eff6ff" : "#f1f5f9", padding: "2px 8px", borderRadius: "12px", fontSize: "12px" }}>
            {jntuaSubjects.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveSubTab("documents")}
          style={{
            padding: "10px 18px",
            border: "none",
            background: "none",
            borderBottom: activeSubTab === "documents" ? "3px solid #2563eb" : "3px solid transparent",
            color: activeSubTab === "documents" ? "#2563eb" : "#64748b",
            fontWeight: "700",
            fontSize: "14px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>📁 Uploaded Documents</span>
          <span style={{ background: activeSubTab === "documents" ? "#eff6ff" : "#f1f5f9", padding: "2px 8px", borderRadius: "12px", fontSize: "12px" }}>
            {totalCount}
          </span>
        </button>
      </div>

      {/* TAB 1: JNTUA SYLLABUS & SUBJECTS */}
      {activeSubTab === "subjects" && (
        <div>
          {/* Search bar for subjects */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
            <div className="search-input-wrapper" style={{ width: "320px" }}>
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="search-input"
                placeholder="Search subject by name, code, or semester..."
                value={subjectSearch}
                onChange={(e) => setSubjectSearch(e.target.value)}
              />
            </div>
            <span style={{ fontSize: "13px", color: "#64748b", fontWeight: "600" }}>
              Curriculum Regulation: <strong style={{ color: "#0f172a" }}>JNTUA R20 / R23</strong>
            </span>
          </div>

          {loading ? (
            <p className="empty-state">Loading JNTUA subjects...</p>
          ) : filteredSubjects.length === 0 ? (
            <p className="empty-state">No JNTUA subjects matched your search.</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
              {filteredSubjects.map((sub) => {
                const isExpanded = expandedUnitCode === sub.code;
                return (
                  <div
                    key={sub.code}
                    style={{
                      background: "#ffffff",
                      borderRadius: "10px",
                      border: "1.5px solid #e2e8f0",
                      padding: "18px",
                      boxShadow: "0 2px 6px rgba(0,0,0,0.03)",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                        <span style={{ background: "#eff6ff", color: "#1d4ed8", padding: "3px 8px", borderRadius: "6px", fontSize: "12px", fontWeight: "800", letterSpacing: "0.5px" }}>
                          {sub.code}
                        </span>
                        <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>
                          {sub.credits} Credits
                        </span>
                      </div>

                      <h4 style={{ fontSize: "15px", fontWeight: "800", color: "#0f172a", margin: "4px 0 6px" }}>
                        {sub.name}
                      </h4>

                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "12px" }}>
                        <span style={{ fontSize: "11px", background: "#f8fafc", color: "#475569", padding: "2px 8px", borderRadius: "4px", border: "1px solid #e2e8f0" }}>
                          📅 {sub.semester}
                        </span>
                        <span style={{ fontSize: "11px", background: "#f8fafc", color: "#475569", padding: "2px 8px", borderRadius: "4px", border: "1px solid #e2e8f0" }}>
                          🏷️ {sub.category}
                        </span>
                      </div>
                    </div>

                    {/* Units breakdown */}
                    <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "10px" }}>
                      <button
                        type="button"
                        onClick={() => setExpandedUnitCode(isExpanded ? null : sub.code)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#2563eb",
                          fontSize: "12px",
                          fontWeight: "700",
                          cursor: "pointer",
                          padding: 0,
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <span>{isExpanded ? "▲ Hide Units Syllabus" : "▼ View 5-Unit Syllabus (JNTUA Outline)"}</span>
                      </button>

                      {isExpanded && sub.units && (
                        <div style={{ marginTop: "10px", background: "#f8fafc", padding: "10px 12px", borderRadius: "6px", fontSize: "12px", color: "#334155" }}>
                          {sub.units.map((u, uIdx) => (
                            <p key={uIdx} style={{ margin: "4px 0", lineHeight: "1.4" }}>
                              <strong>• </strong>{u}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: UPLOADED DOCUMENTS */}
      {activeSubTab === "documents" && (
        <div>
          {/* Department Metrics Cards */}
          <div className="stats-grid" style={{ marginBottom: "20px" }}>
            <div className="stat-card">
              <span className="stat-label">Total Submissions</span>
              <span className="stat-value">{totalCount}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Strictly Accepted</span>
              <span className="stat-value accepted">{acceptedCount} ({complianceRate}%)</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Strictly Rejected</span>
              <span className="stat-value rejected">{rejectedCount}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Pending Analysis</span>
              <span className="stat-value pending">{pendingCount}</span>
            </div>
          </div>

          {/* Search & Filter Toolbar */}
          <div className="dashboard-toolbar">
            <div className="toolbar-controls">
              <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="search-input"
                  placeholder={`Search ${deptInfo.code || "department"} files, types, faculty...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <select
                className="toolbar-filter-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Decisions</option>
                <option value="ACCEPTED">✓ Accepted Only</option>
                <option value="REJECTED">✕ Rejected Only</option>
                <option value="PENDING">⏳ Pending Only</option>
              </select>

              {(searchQuery || statusFilter !== "ALL") && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setSearchQuery("");
                    setStatusFilter("ALL");
                  }}
                >
                  ✕ Reset
                </button>
              )}
            </div>

            <span className="toolbar-count">
              Showing {filteredDocs.length} of {totalCount} records
            </span>
          </div>

          {/* Documents List / Table */}
          {loading ? (
            <p className="empty-state">Loading department uploaded files...</p>
          ) : error ? (
            <div className="error-banner">{error}</div>
          ) : filteredDocs.length === 0 ? (
            <div className="empty-state" style={{ padding: "48px 20px" }}>
              <span className="empty-icon" style={{ fontSize: "42px" }}>📁</span>
              <h4 style={{ fontSize: "16px", fontWeight: "700", color: "#1e293b", margin: "10px 0 6px" }}>
                No documents found for {deptInfo.name || department?.name}
              </h4>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                {searchQuery || statusFilter !== "ALL"
                  ? "Try adjusting your search query or filter options."
                  : "No faculty members have uploaded files for this department yet."}
              </p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Document File</th>
                    <th>Type</th>
                    <th>Submitted By</th>
                    <th>Uploaded Date</th>
                    <th>Decision</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDocs.map((doc) => (
                    <tr key={doc.id}>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "18px" }}>📄</span>
                          <strong>{doc.file_name}</strong>
                        </div>
                      </td>
                      <td>{doc.document_type_name || "Institutional Document"}</td>
                      <td>{doc.uploaded_by_name || doc.uploaded_by_email || "Faculty Member"}</td>
                      <td>{new Date(doc.uploaded_at).toLocaleString()}</td>
                      <td>
                        <StatusBadge status={doc.analysis_status} />
                      </td>
                      <td>
                        <div className="table-actions">
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => {
                              setPdfModalData({
                                id: doc.id,
                                name: doc.file_name,
                                isAccepted: doc.analysis_status === "ACCEPTED",
                              });
                              setPdfModalOpen(true);
                            }}
                          >
                            👁️ View PDF
                          </button>

                          {doc.analysis_status && doc.analysis_status !== "PENDING" && (
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => openComparisonModal(doc.id)}
                            >
                              🔍 Comparison
                            </button>
                          )}

                          {doc.analysis_status === "ACCEPTED" && (
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handleDownload(doc.id, doc.file_name)}
                            >
                              📥 Download
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Comparison Modal */}
      <ComparisonModal
        isOpen={comparisonModalOpen}
        onClose={() => setComparisonModalOpen(false)}
        data={comparisonData}
        canDownload={true}
        onDownload={handleDownload}
      />

      {/* PDF Viewer Modal */}
      <PdfViewerModal
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
        documentId={pdfModalData.id}
        fileName={pdfModalData.name}
        isAccepted={pdfModalData.isAccepted}
        canDownload={true}
        onDownload={handleDownload}
      />
    </div>
  );
}

export default DepartmentDocumentsView;
