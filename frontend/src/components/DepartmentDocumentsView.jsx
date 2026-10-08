import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "./StatusBadge";
import ComparisonModal from "./ComparisonModal";
import PdfViewerModal from "./PdfViewerModal";

function DepartmentDocumentsView({ department, onBack, user }) {
  const [documents, setDocuments] = useState([]);
  const [deptInfo, setDeptInfo] = useState(department || {});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  // Modals
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  useEffect(() => {
    loadDepartmentDocs();
  }, [department]);

  const loadDepartmentDocs = async () => {
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
      setDocuments(res.data.documents || res.data || []);
      if (res.data.department) {
        setDeptInfo(res.data.department);
      }
    } catch (err) {
      console.error("Failed to load department documents:", err);
      setError("Unable to load documents for this department.");
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
            {user?.institution_name || "Institution"}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="panel-header" style={{ marginBottom: "16px" }}>
        <div>
          <h2 style={{ fontSize: "20px", fontWeight: "800", color: "#0f172a", margin: "0 0 6px" }}>
            📂 {deptInfo.name || department?.name}
          </h2>
          <p style={{ fontSize: "13px", color: "var(--text-muted)", margin: 0 }}>
            Showing all uploaded files, syllabi, question papers, and compliance records for this department.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadDepartmentDocs} disabled={loading}>
          ↻ Refresh Files
        </button>
      </div>

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
          Showing {filtered.length} of {totalCount} records
        </span>
      </div>

      {/* Documents List / Table */}
      {loading ? (
        <p className="empty-state">Loading department uploaded files...</p>
      ) : error ? (
        <div className="error-banner">{error}</div>
      ) : filtered.length === 0 ? (
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
              {filtered.map((doc) => (
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
