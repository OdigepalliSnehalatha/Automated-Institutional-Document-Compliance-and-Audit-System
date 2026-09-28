import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function FacultyDashboard({ user }) {
  const [documents, setDocuments] = useState([]);
  const [documentTypes, setDocumentTypes] = useState([]);

  // Upload state
  const [selectedDocTypeId, setSelectedDocTypeId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [feedback, setFeedback] = useState({ error: "", success: "" });

  // Modals state
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  useEffect(() => {
    loadMyDocuments();
    loadDocumentTypes();
  }, []);

  const loadMyDocuments = async () => {
    try {
      const res = await api.get("/faculty/documents");
      setDocuments(res.data);
    } catch (err) {
      console.error("Failed to load faculty documents:", err);
    }
  };

  const loadDocumentTypes = async () => {
    try {
      const res = await api.get("/document-types");
      setDocumentTypes(res.data);
      if (res.data.length > 0 && !selectedDocTypeId) {
        setSelectedDocTypeId(String(res.data[0].id));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setFeedback({ error: "", success: "" });

    if (!selectedFile) {
      setFeedback({ error: "Please select a PDF file to upload.", success: "" });
      return;
    }

    if (!selectedFile.name.toLowerCase().endsWith(".pdf")) {
      setFeedback({ error: "Only valid PDF files are accepted.", success: "" });
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("document_type_id", selectedDocTypeId);
    if (user.department_id) {
      formData.append("department_id", user.department_id);
    }

    setUploading(true);
    try {
      const res = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const uploadedDoc = res.data.document;
      setFeedback({
        error: "",
        success: `Document '${uploadedDoc.file_name}' uploaded successfully! Triggering structural analysis...`,
      });

      // Clear file input
      setSelectedFile(null);
      const fileInput = document.getElementById("pdf-file-input");
      if (fileInput) fileInput.value = "";

      // Automatically trigger structural analysis
      await triggerAnalysis(uploadedDoc.id);
      loadMyDocuments();
    } catch (err) {
      setFeedback({
        error: err.response?.data?.detail || "Upload failed. Please check the file and try again.",
        success: "",
      });
    } finally {
      setUploading(false);
    }
  };

  const triggerAnalysis = async (docId) => {
    setAnalyzingId(docId);
    setFeedback({ error: "", success: "" });
    try {
      const res = await api.post(`/documents/${docId}/analyze`);
      const status = res.data.status;
      setFeedback({
        error: "",
        success: `Structural analysis complete: Decision is ${status}.`,
      });
      loadMyDocuments();

      // Show comparison modal automatically
      openComparisonModal(docId);
    } catch (err) {
      setFeedback({
        error: err.response?.data?.detail || "Structural analysis failed.",
        success: "",
      });
    } finally {
      setAnalyzingId(null);
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

  return (
    <div className="main-content">
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "22px", fontWeight: "700" }}>Faculty Document Upload & Verification</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          Department: <strong>{user.department_name || "General"}</strong> | Upload PDFs to run instant structural validation against Auditor-defined formats.
        </p>
      </div>

      {feedback.error && <div className="alert-message alert-danger">⚠️ {feedback.error}</div>}
      {feedback.success && <div className="alert-message alert-success">✓ {feedback.success}</div>}

      {/* UPLOAD FORM PANEL */}
      <div className="panel">
        <div className="panel-header">
          <h3>Upload Institutional PDF Document</h3>
        </div>

        <form onSubmit={handleUploadSubmit}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
            <div className="form-group">
              <label>Document Type *</label>
              <select
                className="form-select"
                value={selectedDocTypeId}
                onChange={(e) => setSelectedDocTypeId(e.target.value)}
                required
              >
                {documentTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Department</label>
              <input
                type="text"
                className="form-input"
                value={user.department_name ? `${user.department_name}` : "Assigned Department"}
                disabled
              />
            </div>
          </div>

          <div className="form-group">
            <label>Select PDF File *</label>
            <input
              id="pdf-file-input"
              type="file"
              className="form-input"
              accept=".pdf,application/pdf"
              onChange={(e) => setSelectedFile(e.target.files[0])}
              required
            />
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
              Original PDF is securely preserved. File is structurally evaluated against required sections, questions, and marks.
            </p>
          </div>

          <button type="submit" className="btn btn-primary" disabled={uploading || !selectedFile}>
            {uploading ? "Uploading & Analyzing..." : "📤 Upload & Run Structural Analysis"}
          </button>
        </form>
      </div>

      {/* MY DOCUMENTS PANEL */}
      <div className="panel">
        <div className="panel-header">
          <h3>My Submitted Documents ({documents.length})</h3>
          <button className="btn btn-secondary btn-sm" onClick={loadMyDocuments}>
            ↻ Refresh
          </button>
        </div>

        {documents.length === 0 ? (
          <p className="empty-state">You have not uploaded any documents yet.</p>
        ) : (
          <div className="table-wrapper">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Document Type</th>
                  <th>Upload Date</th>
                  <th>Structural Decision</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td><strong>{doc.file_name}</strong></td>
                    <td>{doc.document_type_name || "-"}</td>
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

                        <button
                          className="btn btn-primary btn-sm"
                          disabled={analyzingId === doc.id}
                          onClick={() => triggerAnalysis(doc.id)}
                        >
                          {analyzingId === doc.id ? "Analyzing..." : "⚡ Re-Analyze"}
                        </button>

                        {doc.analysis_status && doc.analysis_status !== "PENDING" && (
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => openComparisonModal(doc.id)}
                          >
                            🔍 Breakdown
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

      {/* Comparison Modal */}
      <ComparisonModal
        isOpen={comparisonModalOpen}
        onClose={() => setComparisonModalOpen(false)}
        data={comparisonData}
        canDownload={false} // Faculty views status only; download is reserved for Auditor & HOD
      />

      {/* PDF Viewer Modal */}
      <PdfViewerModal
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
        documentId={pdfModalData.id}
        fileName={pdfModalData.name}
        isAccepted={pdfModalData.isAccepted}
        canDownload={false}
      />
    </div>
  );
}

export default FacultyDashboard;
