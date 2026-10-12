import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "./StatusBadge";
import ComparisonModal from "./ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function DepartmentDocumentsView({ department, onBack, user }) {
  const [documents, setDocuments] = useState([]);
  const [curriculum, setCurriculum] = useState([]);
  const [deptInfo, setDeptInfo] = useState(department || {});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeSubTab, setActiveSubTab] = useState("curriculum"); // "curriculum" | "documents"

  // Semester filtering & search for curriculum
  const [selectedSemester, setSelectedSemester] = useState("ALL"); // "ALL" | 1..8
  const [curriculumSearch, setCurriculumSearch] = useState("");

  // Search & Filter for Documents
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

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
      setCurriculum(res.data.curriculum || []);
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

  const handleDownload = (docId) => {
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

  // Filter curriculum semesters and search query
  const qCurriculum = curriculumSearch.toLowerCase().trim();

  const filteredCurriculum = curriculum
    .filter((sem) => {
      if (selectedSemester !== "ALL" && sem.semester_num !== Number(selectedSemester)) {
        return false;
      }
      if (!qCurriculum) return true;

      const hasMatchingSubject = sem.subjects.some((s) => s.toLowerCase().includes(qCurriculum));
      const hasMatchingLab = sem.labs.some((l) => l.toLowerCase().includes(qCurriculum));
      const hasMatchingLabel = sem.semester_label.toLowerCase().includes(qCurriculum);

      return hasMatchingSubject || hasMatchingLab || hasMatchingLabel;
    })
    .map((sem) => {
      if (!qCurriculum) return sem;
      return {
        ...sem,
        subjects: sem.subjects.filter((s) => s.toLowerCase().includes(qCurriculum)),
        labs: sem.labs.filter((l) => l.toLowerCase().includes(qCurriculum)),
      };
    });

  // Total counts across all 8 semesters
  const totalSubjectsCount = curriculum.reduce((acc, sem) => acc + (sem.subjects?.length || 0), 0);
  const totalLabsCount = curriculum.reduce((acc, sem) => acc + (sem.labs?.length || 0), 0);

  return (
    <div className="panel" style={{ animation: "fadeIn 0.25s ease-out" }}>
      {/* Top Navigation & Breadcrumb */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "18px",
          borderBottom: "1px solid var(--border-color)",
          paddingBottom: "14px",
        }}
      >
        <button
          className="btn btn-secondary btn-sm"
          onClick={onBack}
          style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700" }}
        >
          <span>← Back to Departments</span>
        </button>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span className="branch-pill" style={{ fontSize: "13px", padding: "4px 12px", fontWeight: "800" }}>
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
            Official 4-Year JNTUA Academic Curriculum (Semesters 1 to 8: All Subjects & Labs)
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadDepartmentData} disabled={loading}>
          ↻ Refresh
        </button>
      </div>

      {/* Sub-Tabs: Curriculum (Semesters 1-8) vs Uploaded Documents */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", borderBottom: "2px solid #e2e8f0" }}>
        <button
          type="button"
          onClick={() => setActiveSubTab("curriculum")}
          style={{
            padding: "10px 18px",
            border: "none",
            background: "none",
            borderBottom: activeSubTab === "curriculum" ? "3px solid #2563eb" : "3px solid transparent",
            color: activeSubTab === "curriculum" ? "#2563eb" : "#64748b",
            fontWeight: "700",
            fontSize: "14px",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>📚 1st Year to 4th Year Curriculum (Sem 1 - 8)</span>
          <span
            style={{
              background: activeSubTab === "curriculum" ? "#eff6ff" : "#f1f5f9",
              color: activeSubTab === "curriculum" ? "#2563eb" : "#64748b",
              padding: "2px 8px",
              borderRadius: "12px",
              fontSize: "12px",
              fontWeight: "700",
            }}
          >
            {curriculum.length} Semesters
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
          <span>📁 Department Uploaded Documents</span>
          <span
            style={{
              background: activeSubTab === "documents" ? "#eff6ff" : "#f1f5f9",
              color: activeSubTab === "documents" ? "#2563eb" : "#64748b",
              padding: "2px 8px",
              borderRadius: "12px",
              fontSize: "12px",
              fontWeight: "700",
            }}
          >
            {totalCount}
          </span>
        </button>
      </div>

      {/* TAB 1: 1ST YEAR 1ST SEMESTER TO 4TH YEAR 8TH SEMESTER CURRICULUM */}
      {activeSubTab === "curriculum" && (
        <div>
          {/* Quick Summary Banner */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              background: "#f8fafc",
              border: "1px solid #e2e8f0",
              borderRadius: "8px",
              padding: "12px 18px",
              marginBottom: "16px",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "13px", color: "#334155" }}>
                Total Semesters: <strong>8 Semesters (4 Years)</strong>
              </span>
              <span style={{ color: "#cbd5e1" }}>•</span>
              <span style={{ fontSize: "13px", color: "#334155" }}>
                Theory Subjects: <strong style={{ color: "#1d4ed8" }}>{totalSubjectsCount}</strong>
              </span>
              <span style={{ color: "#cbd5e1" }}>•</span>
              <span style={{ fontSize: "13px", color: "#334155" }}>
                Laboratory Courses: <strong style={{ color: "#059669" }}>{totalLabsCount}</strong>
              </span>
            </div>
            <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>
              Regulation: <strong>JNTUA R20 / R23</strong>
            </span>
          </div>

          {/* Search & Semester Pills Filter */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "18px",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            {/* Search Input */}
            <div className="search-input-wrapper" style={{ width: "320px" }}>
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="search-input"
                placeholder="Search subject or lab name..."
                value={curriculumSearch}
                onChange={(e) => setCurriculumSearch(e.target.value)}
              />
            </div>

            {/* Semester Quick Filter Buttons */}
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
              <button
                type="button"
                onClick={() => setSelectedSemester("ALL")}
                style={{
                  padding: "6px 12px",
                  borderRadius: "6px",
                  border: selectedSemester === "ALL" ? "1.5px solid #2563eb" : "1px solid #e2e8f0",
                  background: selectedSemester === "ALL" ? "#eff6ff" : "#ffffff",
                  color: selectedSemester === "ALL" ? "#1d4ed8" : "#475569",
                  fontSize: "12px",
                  fontWeight: selectedSemester === "ALL" ? "700" : "500",
                  cursor: "pointer",
                }}
              >
                All 8 Semesters
              </button>

              {[
                { num: 1, label: "I-I (Sem 1)" },
                { num: 2, label: "I-II (Sem 2)" },
                { num: 3, label: "II-I (Sem 3)" },
                { num: 4, label: "II-II (Sem 4)" },
                { num: 5, label: "III-I (Sem 5)" },
                { num: 6, label: "III-II (Sem 6)" },
                { num: 7, label: "IV-I (Sem 7)" },
                { num: 8, label: "IV-II (Sem 8)" },
              ].map((s) => (
                <button
                  key={s.num}
                  type="button"
                  onClick={() => setSelectedSemester(s.num)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: "6px",
                    border: selectedSemester === s.num ? "1.5px solid #2563eb" : "1px solid #e2e8f0",
                    background: selectedSemester === s.num ? "#eff6ff" : "#ffffff",
                    color: selectedSemester === s.num ? "#1d4ed8" : "#475569",
                    fontSize: "12px",
                    fontWeight: selectedSemester === s.num ? "700" : "500",
                    cursor: "pointer",
                  }}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Curriculum List (Semesters 1 through 8) */}
          {loading ? (
            <p className="empty-state">Loading JNTUA curriculum...</p>
          ) : filteredCurriculum.length === 0 ? (
            <div className="empty-state">
              <span className="empty-icon" style={{ fontSize: "36px" }}>🔍</span>
              <p style={{ margin: "8px 0 0", color: "#64748b" }}>
                No subjects or labs matched "{curriculumSearch}".
              </p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {filteredCurriculum.map((sem) => (
                <div
                  key={sem.semester_num}
                  style={{
                    background: "#ffffff",
                    borderRadius: "10px",
                    border: "1.5px solid #e2e8f0",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.03)",
                    overflow: "hidden",
                  }}
                >
                  {/* Semester Card Header */}
                  <div
                    style={{
                      background: "#f8fafc",
                      padding: "14px 20px",
                      borderBottom: "1px solid #e2e8f0",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: "10px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span
                        style={{
                          background: "#2563eb",
                          color: "#ffffff",
                          fontSize: "12px",
                          fontWeight: "800",
                          padding: "3px 10px",
                          borderRadius: "6px",
                          letterSpacing: "0.5px",
                        }}
                      >
                        Sem {sem.semester_num}
                      </span>
                      <h3 style={{ fontSize: "16px", fontWeight: "800", color: "#0f172a", margin: 0 }}>
                        {sem.semester_label}
                      </h3>
                      <span
                        style={{
                          fontSize: "11px",
                          background: "#e2e8f0",
                          color: "#475569",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontWeight: "600",
                        }}
                      >
                        {sem.year}
                      </span>
                    </div>

                    <div style={{ display: "flex", gap: "8px" }}>
                      <span
                        style={{
                          fontSize: "12px",
                          background: "#eff6ff",
                          color: "#1d4ed8",
                          padding: "3px 10px",
                          borderRadius: "12px",
                          fontWeight: "700",
                        }}
                      >
                        📘 {sem.subjects?.length || 0} Theory Subjects
                      </span>
                      <span
                        style={{
                          fontSize: "12px",
                          background: "#ecfdf5",
                          color: "#059669",
                          padding: "3px 10px",
                          borderRadius: "12px",
                          fontWeight: "700",
                        }}
                      >
                        🧪 {sem.labs?.length || 0} Labs
                      </span>
                    </div>
                  </div>

                  {/* Semester Content: Subjects and Labs with Names Only */}
                  <div
                    style={{
                      padding: "18px 20px",
                      display: "grid",
                      gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                      gap: "20px",
                    }}
                  >
                    {/* Column 1: Theory Subjects (Names Only) */}
                    <div
                      style={{
                        background: "#fafafa",
                        border: "1px solid #f1f5f9",
                        borderRadius: "8px",
                        padding: "16px",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          marginBottom: "12px",
                          paddingBottom: "8px",
                          borderBottom: "1.5px solid #e2e8f0",
                        }}
                      >
                        <span style={{ fontSize: "16px" }}>📖</span>
                        <h4 style={{ fontSize: "14px", fontWeight: "800", color: "#1e293b", margin: 0 }}>
                          Theory Subjects (Names Only)
                        </h4>
                      </div>

                      {(!sem.subjects || sem.subjects.length === 0) ? (
                        <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0 }}>No subjects listed.</p>
                      ) : (
                        <ol
                          style={{
                            margin: 0,
                            paddingLeft: "20px",
                            display: "flex",
                            flexDirection: "column",
                            gap: "8px",
                          }}
                        >
                          {sem.subjects.map((subjName, idx) => (
                            <li
                              key={idx}
                              style={{
                                fontSize: "13px",
                                fontWeight: "600",
                                color: "#1e293b",
                                lineHeight: "1.4",
                              }}
                            >
                              {subjName}
                            </li>
                          ))}
                        </ol>
                      )}
                    </div>

                    {/* Column 2: Laboratories (Names Only) */}
                    <div
                      style={{
                        background: "#f0fdf4",
                        border: "1px solid #dcfce7",
                        borderRadius: "8px",
                        padding: "16px",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          marginBottom: "12px",
                          paddingBottom: "8px",
                          borderBottom: "1.5px solid #bbf7d0",
                        }}
                      >
                        <span style={{ fontSize: "16px" }}>🧪</span>
                        <h4 style={{ fontSize: "14px", fontWeight: "800", color: "#065f46", margin: 0 }}>
                          Laboratory Courses (Names Only)
                        </h4>
                      </div>

                      {(!sem.labs || sem.labs.length === 0) ? (
                        <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0 }}>No laboratory courses listed.</p>
                      ) : (
                        <ol
                          style={{
                            margin: 0,
                            paddingLeft: "20px",
                            display: "flex",
                            flexDirection: "column",
                            gap: "8px",
                          }}
                        >
                          {sem.labs.map((labName, idx) => (
                            <li
                              key={idx}
                              style={{
                                fontSize: "13px",
                                fontWeight: "600",
                                color: "#065f46",
                                lineHeight: "1.4",
                              }}
                            >
                              {labName}
                            </li>
                          ))}
                        </ol>
                      )}
                    </div>
                  </div>
                </div>
              ))}
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
                No documents uploaded for {deptInfo.name || department?.name}
              </h4>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                {searchQuery || statusFilter !== "ALL"
                  ? "Try adjusting your search query or filter options."
                  : "All prototype test files have been removed. When faculty upload verified documents, they will appear here."}
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
                              onClick={() => handleDownload(doc.id)}
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
