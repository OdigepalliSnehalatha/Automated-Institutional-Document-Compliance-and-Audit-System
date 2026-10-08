import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function HodDashboard({ user, activeTab: propActiveTab, onTabChange }) {
  const [internalActiveTab, setInternalActiveTab] = useState("overview"); // "overview" | "all" | "accepted" | "branches"
  const activeTab = propActiveTab || internalActiveTab;
  const setActiveTab = (tab) => {
    setInternalActiveTab(tab);
    if (onTabChange) onTabChange(tab);
  };
  const [documents, setDocuments] = useState([]);
  const [acceptedDocs, setAcceptedDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modals state
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");


  useEffect(() => {
    loadDepartmentDocuments();
    loadAcceptedDocuments();
  }, []);

  const loadDepartmentDocuments = async () => {
    setLoading(true);
    try {
      const res = await api.get("/hod/documents");
      setDocuments(res.data);
    } catch (err) {
      console.error("Failed to load department documents:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadAcceptedDocuments = async () => {
    try {
      const res = await api.get("/hod/accepted-documents");
      setAcceptedDocs(res.data);
    } catch (err) {
      console.error("Failed to load accepted documents:", err);
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

  // Stats calculation
  const totalCount = documents.length;
  const acceptedCount = documents.filter((d) => d.analysis_status === "ACCEPTED").length;
  const rejectedCount = documents.filter((d) => d.analysis_status === "REJECTED").length;
  const pendingCount = documents.filter((d) => !d.analysis_status || d.analysis_status === "PENDING").length;

  return (
    <div className="main-content">
      {/* VIEW 1: DEPARTMENT OVERVIEW */}
      {activeTab === "overview" && (
        <div>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Department Submissions</span>
              <span className="stat-value">{totalCount}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Strictly Accepted</span>
              <span className="stat-value accepted">{acceptedCount}</span>
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

          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Recent Department Activity</h3>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Submissions in {user.department_name || "Department"}
                </span>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={loadDepartmentDocuments} disabled={loading}>
                ↻ Refresh
              </button>
            </div>

            {documents.length === 0 ? (
              <p className="empty-state">No submissions recorded in this department yet.</p>
            ) : (
              <div className="table-wrapper">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Type</th>
                      <th>Submitted By</th>
                      <th>Uploaded Date</th>
                      <th>Decision</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.slice(0, 5).map((doc) => (
                      <tr key={doc.id}>
                        <td><strong>{doc.file_name}</strong></td>
                        <td>{doc.document_type_name || "-"}</td>
                        <td>{doc.uploaded_by_name || "Faculty Member"}</td>
                        <td>{new Date(doc.uploaded_at).toLocaleString()}</td>
                        <td><StatusBadge status={doc.analysis_status} /></td>
                        <td>
                          <div className="table-actions">
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => {
                                setPdfModalData({ id: doc.id, name: doc.file_name, isAccepted: doc.analysis_status === "ACCEPTED" });
                                setPdfModalOpen(true);
                              }}
                            >
                              👁️ View PDF
                            </button>
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
        </div>
      )}

      {/* VIEW 4: BRANCHES & GUIDELINES */}
      {activeTab === "branches" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Institutional Department & Branch Guidelines</h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Overview of supported branches in the compliance system
              </p>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginBottom: "20px" }}>
            {[
              { code: "CAI", name: "Computer Artificial Intelligence" },
              { code: "CSE", name: "Computer Science and Engineering" },
              { code: "CSD", name: "Computer Science and Design" },
              { code: "CSM", name: "CSE (AI & Machine Learning)" },
              { code: "CSE-AIML", name: "CSE - AI & ML Specialization" },
              { code: "ECE", name: "Electronics & Communication Eng." },
              { code: "ME", name: "Mechanical Engineering" },
              { code: "CE", name: "Civil Engineering" },
            ].map((b) => (
              <div key={b.code} style={{ padding: "14px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <span className="branch-pill" style={{ marginBottom: "6px" }}>{b.code}</span>
                <p style={{ margin: "4px 0 0", fontSize: "13px", fontWeight: "700", color: "#0f172a" }}>{b.name}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "all" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Faculty Document Submissions</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Total submissions: {documents.length}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadDepartmentDocuments} disabled={loading}>
              ↻ Refresh
            </button>
          </div>

          {/* Search & Filter Toolbar */}
          {documents.length > 0 && (
            <div className="dashboard-toolbar">
              <div className="toolbar-controls">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search document name, type, faculty..."
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
                    title="Clear filters"
                  >
                    ✕ Reset
                  </button>
                )}
              </div>

              <span className="toolbar-count">
                Showing{" "}
                {
                  documents.filter((doc) => {
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
                  }).length
                }{" "}
                of {documents.length}
              </span>
            </div>
          )}

          {documents.length === 0 ? (
            <p className="empty-state">No documents submitted in this department yet.</p>
          ) : (
            (() => {
              const filtered = documents.filter((doc) => {
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

              if (filtered.length === 0) {
                return (
                  <p className="empty-state">No documents match your search or filter criteria.</p>
                );
              }

              return (
                <div className="table-wrapper">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Document</th>
                        <th>Document Type</th>
                        <th>Submitted By</th>
                        <th>Uploaded Date</th>
                        <th>Structural Decision</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((doc) => (
                        <tr key={doc.id}>
                          <td><strong>{doc.file_name}</strong></td>
                          <td>{doc.document_type_name || "-"}</td>
                          <td>{doc.uploaded_by_name || "Faculty Member"}</td>
                          <td>{new Date(doc.uploaded_at).toLocaleString()}</td>
                          <td><StatusBadge status={doc.analysis_status} /></td>
                          <td>
                            <div className="table-actions">
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => {
                                  setPdfModalData({ id: doc.id, name: doc.file_name, isAccepted: doc.analysis_status === "ACCEPTED" });
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
              );
            })()
          )}
        </div>
      )}

      {activeTab === "accepted" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Department Accepted & Compliant Documents</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Verified files available for official download: {acceptedDocs.length}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadAcceptedDocuments}>
              ↻ Refresh
            </button>
          </div>

          {/* Search Toolbar for Accepted */}
          {acceptedDocs.length > 0 && (
            <div className="dashboard-toolbar">
              <div className="toolbar-controls">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search verified file, type, submitter..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                {searchQuery && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setSearchQuery("")}
                    title="Clear search"
                  >
                    ✕ Reset
                  </button>
                )}
              </div>
              <span className="toolbar-count">
                Showing{" "}
                {
                  acceptedDocs.filter((doc) => {
                    const q = searchQuery.toLowerCase();
                    return (
                      !q ||
                      doc.file_name.toLowerCase().includes(q) ||
                      (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                      (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q))
                    );
                  }).length
                }{" "}
                of {acceptedDocs.length}
              </span>
            </div>
          )}

          {acceptedDocs.length === 0 ? (
            <p className="empty-state">No accepted documents for this department yet.</p>
          ) : (
            (() => {
              const filtered = acceptedDocs.filter((doc) => {
                const q = searchQuery.toLowerCase();
                return (
                  !q ||
                  doc.file_name.toLowerCase().includes(q) ||
                  (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                  (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q))
                );
              });

              if (filtered.length === 0) {
                return (
                  <p className="empty-state">No verified documents match your search query.</p>
                );
              }

              return (
                <div className="table-wrapper">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Document</th>
                        <th>Document Type</th>
                        <th>Submitted By</th>
                        <th>Analyzed At</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((doc) => (
                        <tr key={doc.id}>
                          <td><strong>{doc.file_name}</strong></td>
                          <td>{doc.document_type_name}</td>
                          <td>{doc.uploaded_by_name}</td>
                          <td>{doc.analyzed_at ? new Date(doc.analyzed_at).toLocaleString() : "-"}</td>
                          <td><StatusBadge status="ACCEPTED" /></td>
                          <td>
                            <div className="table-actions">
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => {
                                  setPdfModalData({ id: doc.id, name: doc.file_name, isAccepted: true });
                                  setPdfModalOpen(true);
                                }}
                              >
                                👁️ View PDF
                              </button>
                              <button
                                className="btn btn-success btn-sm"
                                onClick={() => handleDownload(doc.id, doc.file_name)}
                              >
                                📥 Download PDF
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })()
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

export default HodDashboard;
