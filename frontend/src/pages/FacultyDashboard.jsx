import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function FacultyDashboard({ user, activeTab: propActiveTab, onTabChange }) {
  const [internalActiveTab, setInternalActiveTab] = useState("upload"); // upload | submissions | guidelines
  const activeTab = propActiveTab || internalActiveTab;
  const setActiveTab = (tab) => {
    setInternalActiveTab(tab);
    if (onTabChange) onTabChange(tab);
  };
  const [documents, setDocuments] = useState([]);
  const [documentTypes, setDocumentTypes] = useState([]);
  const [departments, setDepartments] = useState([]);

  // Upload state
  const [selectedDocTypeId, setSelectedDocTypeId] = useState("");
  const [selectedDeptId, setSelectedDeptId] = useState(
    user.department_id ? String(user.department_id) : "1"
  );
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [analyzingId, setAnalyzingId] = useState(null);
  const [feedback, setFeedback] = useState({ error: "", success: "" });

  // Modals state
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  // Filter & Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");


  useEffect(() => {
    loadMyDocuments();
    loadDocumentTypes();
    loadDepartments();
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
      console.error("Failed to load document types:", err);
    }
  };

  const loadDepartments = async () => {
    try {
      const res = await api.get("/departments");
      setDepartments(res.data);
      if (res.data.length > 0 && !selectedDeptId) {
        setSelectedDeptId(String(res.data[0].id));
      }
    } catch (err) {
      console.error("Failed to load departments:", err);
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
    formData.append("department_id", selectedDeptId || "1");

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

  const handleDeleteDocument = async (docId, fileName) => {
    if (!window.confirm(`Are you sure you want to delete the uploaded document:\n"${fileName}"?\n\nThis will permanently remove the file, audit records, and verification results.`)) {
      return;
    }
    try {
      const res = await api.delete(`/documents/${docId}`);
      setFeedback({
        success: res.data?.message || `Document "${fileName}" deleted successfully.`,
        error: ""
      });
      loadMyDocuments();
    } catch (err) {
      console.error("Delete failed:", err);
      const msg = err.response?.data?.detail || "Failed to delete document. Please try again.";
      setFeedback({ error: msg, success: "" });
      alert(msg);
    }
  };

  return (
    <div className="main-content">
      <div style={{ marginBottom: "24px" }}>
        <h2 style={{ fontSize: "22px", fontWeight: "700" }}>Faculty Document Upload & Verification</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          Support for all institutional branches (CSE, CSD, CSM, CSE-AIML, ECE, ME, CE) | Upload PDFs for instant structural compliance checking.
        </p>
      </div>

      {feedback.error && <div className="alert-message alert-danger">⚠️ {feedback.error}</div>}
      {feedback.success && <div className="alert-message alert-success">✓ {feedback.success}</div>}

      {/* UPLOAD FORM PANEL */}
      {(activeTab === "upload" || activeTab === "overview") && (
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
                <label>Branch / Department *</label>
                <select
                  className="form-select"
                  value={selectedDeptId}
                  onChange={(e) => setSelectedDeptId(e.target.value)}
                  required
                >
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} - {d.name}
                    </option>
                  ))}
                </select>
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
      )}

      {/* MY DOCUMENTS PANEL */}
      {(activeTab === "submissions" || activeTab === "overview" || activeTab === "upload") && (
      <div className="panel">
        <div className="panel-header">
          <div>
            <h3>My Submitted Documents</h3>
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
              Total uploads: {documents.length}
            </span>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={loadMyDocuments}>
            ↻ Refresh
          </button>
        </div>

        {/* Toolbar: Search & Status Filter */}
        {documents.length > 0 && (
          <div className="dashboard-toolbar">
            <div className="toolbar-controls">
              <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search file, document type, branch..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <select
                className="toolbar-filter-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
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
                    (doc.department_code && doc.department_code.toLowerCase().includes(q));
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
          <p className="empty-state">You have not uploaded any documents yet.</p>
        ) : (
          (() => {
            const filtered = documents.filter((doc) => {
              const q = searchQuery.toLowerCase();
              const matchesSearch =
                !q ||
                doc.file_name.toLowerCase().includes(q) ||
                (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                (doc.department_code && doc.department_code.toLowerCase().includes(q));
              const matchesStatus =
                statusFilter === "ALL" ||
                doc.analysis_status === statusFilter ||
                (statusFilter === "PENDING" && (!doc.analysis_status || doc.analysis_status === "PENDING"));
              return matchesSearch && matchesStatus;
            });

            if (filtered.length === 0) {
              return (
                <p className="empty-state">
                  No documents match your search or filter criteria.
                </p>
              );
            }

            return (
              <div className="table-wrapper">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>File Name</th>
                      <th>Document Type</th>
                      <th>Branch</th>
                      <th>Upload Date</th>
                      <th>Structural Decision</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((doc) => (
                      <tr key={doc.id}>
                        <td><strong>{doc.file_name}</strong></td>
                        <td>{doc.document_type_name || "-"}</td>
                        <td>
                          <span className="branch-pill">
                            {doc.department_code || doc.department_name || "General"}
                          </span>
                        </td>
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

                            <button
                              className="btn btn-danger btn-sm"
                              style={{ color: "#ef4444", borderColor: "rgba(239, 68, 68, 0.4)", background: "rgba(239, 68, 68, 0.08)", padding: "4px 8px" }}
                              onClick={() => handleDeleteDocument(doc.id, doc.file_name)}
                              title={`Delete ${doc.file_name}`}
                            >
                              🗑️ Delete
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

      {/* VIEW 3: COMPLIANCE GUIDELINES PANEL */}
      {(activeTab === "guidelines" || activeTab === "rules") && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Institutional Document Compliance Rules & Checklist</h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Follow these strict structural formatting requirements to ensure 100% automated verification
              </p>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "20px" }}>
            {/* Question Paper Checklist */}
            <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <span style={{ fontSize: "20px" }}>📄</span>
                <h4 style={{ margin: 0, fontSize: "15px", fontWeight: "700" }}>Question Paper Requirements</h4>
              </div>
              <ul style={{ paddingLeft: "18px", fontSize: "13px", lineHeight: "1.6", color: "#334155" }}>
                <li><strong>Header</strong>: Institute Name, Semester, Branch, Subject Name & Code, Max Marks, Time.</li>
                <li><strong>Mid Examination</strong>: Part A must have exactly 5 questions (2 marks each); Part B must have 6 questions (10 marks each).</li>
                <li><strong>Semester Examination</strong>: Part A must have 10 questions (2M); Part B must have 10 questions (10M).</li>
                <li><strong>Strict Boolean Decision</strong>: Any missing question number or marks pattern results in instant <code>REJECTED</code>.</li>
              </ul>
            </div>

            {/* Course Structure Checklist */}
            <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <span style={{ fontSize: "20px" }}>📚</span>
                <h4 style={{ margin: 0, fontSize: "15px", fontWeight: "700" }}>Course Structure Requirements</h4>
              </div>
              <ul style={{ paddingLeft: "18px", fontSize: "13px", lineHeight: "1.6", color: "#334155" }}>
                <li><strong>Header</strong>: Institution & Department Heading, Course Name, Course Code.</li>
                <li><strong>Curriculum Units</strong>: All 5 structural sections must be present: Unit 1, Unit 2, Unit 3, Unit 4, Unit 5.</li>
                <li><strong>Topic Sections</strong>: Each unit must be followed by its respective syllabus topic body.</li>
                <li><strong>Order</strong>: Units must appear in chronological sequential order.</li>
              </ul>
            </div>

            {/* Question Bank Checklist */}
            <div style={{ padding: "20px", background: "#f8fafc", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <span style={{ fontSize: "20px" }}>📑</span>
                <h4 style={{ margin: 0, fontSize: "15px", fontWeight: "700" }}>Question Bank Requirements</h4>
              </div>
              <ul style={{ paddingLeft: "18px", fontSize: "13px", lineHeight: "1.6", color: "#334155" }}>
                <li><strong>Header</strong>: College Name, Course Name, Course Code, Semester.</li>
                <li><strong>Units 1 to 5</strong>: Each unit must contain both Part A (10 x 2M questions) and Part B (10 x 10M questions).</li>
                <li><strong>Marks Annotation</strong>: Marks pattern must be clearly indicated for each question.</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Comparison Modal */}
      <ComparisonModal
        isOpen={comparisonModalOpen}
        onClose={() => setComparisonModalOpen(false)}
        data={comparisonData}
        canDownload={false}
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
