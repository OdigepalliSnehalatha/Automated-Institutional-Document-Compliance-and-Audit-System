import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function HodDashboard({ user }) {
  const [activeTab, setActiveTab] = useState("all"); // "all" | "accepted"
  const [documents, setDocuments] = useState([]);
  const [acceptedDocs, setAcceptedDocs] = useState([]);
  const [loading, setLoading] = useState(false);

  // Modals state
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

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
      <div style={{ marginBottom: "20px" }}>
        <h2 style={{ fontSize: "22px", fontWeight: "700" }}>
          HOD Dashboard – {user.department_name || "Department"}
        </h2>
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          Monitor structural compliance for department submissions and access verified accepted documents.
        </p>
      </div>

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

      <div className="tab-nav">
        <button
          className={`tab-btn ${activeTab === "all" ? "active" : ""}`}
          onClick={() => setActiveTab("all")}
        >
          📄 All Department Submissions ({documents.length})
        </button>
        <button
          className={`tab-btn ${activeTab === "accepted" ? "active" : ""}`}
          onClick={() => setActiveTab("accepted")}
        >
          ✓ Accepted Official PDFs ({acceptedDocs.length})
        </button>
      </div>

      {activeTab === "all" && (
        <div className="panel">
          <div className="panel-header">
            <h3>Faculty Document Submissions</h3>
            <button className="btn btn-secondary btn-sm" onClick={loadDepartmentDocuments} disabled={loading}>
              ↻ Refresh
            </button>
          </div>

          {documents.length === 0 ? (
            <p className="empty-state">No documents submitted in this department yet.</p>
          ) : (
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
                  {documents.map((doc) => (
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
          )}
        </div>
      )}

      {activeTab === "accepted" && (
        <div className="panel">
          <div className="panel-header">
            <h3>Department Accepted & Compliant Documents</h3>
            <button className="btn btn-secondary btn-sm" onClick={loadAcceptedDocuments}>
              ↻ Refresh
            </button>
          </div>

          {acceptedDocs.length === 0 ? (
            <p className="empty-state">No accepted documents for this department yet.</p>
          ) : (
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
                  {acceptedDocs.map((doc) => (
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
