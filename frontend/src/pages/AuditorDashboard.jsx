import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";

function AuditorDashboard({ user }) {
  const [activeTab, setActiveTab] = useState("overview"); // overview | formats | submissions | accepted
  const [stats, setStats] = useState(null);
  const [recentSubmissions, setRecentSubmissions] = useState([]);
  const [formats, setFormats] = useState([]);
  const [documentTypes, setDocumentTypes] = useState([]);
  const [departments, setDepartments] = useState([]);

  // Format Builder State
  const [selectedDocTypeId, setSelectedDocTypeId] = useState("");
  const [examType, setExamType] = useState("Mid Examination");
  const [selectedDeptId, setSelectedDeptId] = useState("");
  const [formatName, setFormatName] = useState("");
  const [instructions, setInstructions] = useState("");
  const [requirements, setRequirements] = useState([
    {
      requirement_name: "",
      requirement_type: "text",
      requirement_value: "",
      is_required: true,
      display_order: 1,
    },
  ]);

  // Modals state
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  // Search & Filter state
  const [subSearchQuery, setSubSearchQuery] = useState("");
  const [subStatusFilter, setSubStatusFilter] = useState("ALL");
  const [subDeptFilter, setSubDeptFilter] = useState("ALL");
  const [formatSearchQuery, setFormatSearchQuery] = useState("");

  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState({ error: "", success: "" });


  useEffect(() => {
    loadDashboardData();
    loadDocumentTypes();
    loadDepartments();
    loadFormats();
  }, []);

  const loadDashboardData = async () => {
    try {
      const res = await api.get("/auditor/dashboard");
      setStats(res.data.overview);
      setRecentSubmissions(res.data.recent_submissions);
    } catch (err) {
      console.error("Failed to load auditor dashboard:", err);
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

  const loadDepartments = async () => {
    try {
      const res = await api.get("/departments");
      setDepartments(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadFormats = async () => {
    try {
      const res = await api.get("/formats");
      setFormats(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  // Preset Handlers
  const selectedDocTypeName = documentTypes.find((t) => String(t.id) === String(selectedDocTypeId))?.name || "";

  const applyCourseStructurePreset = () => {
    setFormatName("Standard Institutional Course Structure Format");
    setInstructions("Course structure format enforcing college header, course identification, and Units 1-5 structural sections.");
    setRequirements([
      { requirement_name: "College Name", requirement_type: "header", requirement_value: "College / Institute header", is_required: true, display_order: 1 },
      { requirement_name: "Course Name", requirement_type: "field", requirement_value: "Course name", is_required: true, display_order: 2 },
      { requirement_name: "Course Code", requirement_type: "field", requirement_value: "Course code", is_required: true, display_order: 3 },
      { requirement_name: "Unit 1 Heading", requirement_type: "heading", requirement_value: "Unit 1", is_required: true, display_order: 4 },
      { requirement_name: "Unit 1 Topics", requirement_type: "section", requirement_value: "Unit 1 topics", is_required: true, display_order: 5 },
      { requirement_name: "Unit 2 Heading", requirement_type: "heading", requirement_value: "Unit 2", is_required: true, display_order: 6 },
      { requirement_name: "Unit 2 Topics", requirement_type: "section", requirement_value: "Unit 2 topics", is_required: true, display_order: 7 },
      { requirement_name: "Unit 3 Heading", requirement_type: "heading", requirement_value: "Unit 3", is_required: true, display_order: 8 },
      { requirement_name: "Unit 3 Topics", requirement_type: "section", requirement_value: "Unit 3 topics", is_required: true, display_order: 9 },
      { requirement_name: "Unit 4 Heading", requirement_type: "heading", requirement_value: "Unit 4", is_required: true, display_order: 10 },
      { requirement_name: "Unit 4 Topics", requirement_type: "section", requirement_value: "Unit 4 topics", is_required: true, display_order: 11 },
      { requirement_name: "Unit 5 Heading", requirement_type: "heading", requirement_value: "Unit 5", is_required: true, display_order: 12 },
      { requirement_name: "Unit 5 Topics", requirement_type: "section", requirement_value: "Unit 5 topics", is_required: true, display_order: 13 },
    ]);
  };

  const applyQuestionBankPreset = () => {
    setFormatName("Standard Institutional Question Bank Format");
    setInstructions("Question bank requiring College Name, Course Details, Semester, and Units 1-5 with Part A (10 x 2M) and Part B (10 x 10M).");
    const reqs = [
      { requirement_name: "College Name", requirement_type: "header", requirement_value: "College Name", is_required: true, display_order: 1 },
      { requirement_name: "Course Name", requirement_type: "field", requirement_value: "Course Name", is_required: true, display_order: 2 },
      { requirement_name: "Course Code", requirement_type: "field", requirement_value: "Course Code", is_required: true, display_order: 3 },
      { requirement_name: "Semester", requirement_type: "field", requirement_value: "Semester", is_required: true, display_order: 4 },
    ];
    let order = 5;
    for (let u = 1; u <= 5; u++) {
      reqs.push({ requirement_name: `Unit ${u} Heading`, requirement_type: "heading", requirement_value: `Unit ${u}`, is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part A`, requirement_type: "part a structure", requirement_value: "Part A", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part A Questions`, requirement_type: "question_count", requirement_value: "10", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part A Marks Per Question`, requirement_type: "marks", requirement_value: "2", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part B`, requirement_type: "part b structure", requirement_value: "Part B", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part B Questions`, requirement_type: "question_count", requirement_value: "10", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part B Marks Per Question`, requirement_type: "marks", requirement_value: "10", is_required: true, display_order: order++ });
    }
    setRequirements(reqs);
  };

  const applyQuestionPaperPreset = (type) => {
    const isMid = type === "Mid Examination";
    setFormatName(`Standard ${type} Question Paper Format`);
    setInstructions(`Institutional structural format for ${type} question paper.`);
    setRequirements([
      { requirement_name: "College Header", requirement_type: "header", requirement_value: "College header", is_required: true, display_order: 1 },
      { requirement_name: "Semester", requirement_type: "field", requirement_value: "Semester", is_required: true, display_order: 2 },
      { requirement_name: "B.Tech", requirement_type: "field", requirement_value: "B.Tech", is_required: true, display_order: 3 },
      { requirement_name: "Examination Type", requirement_type: "field", requirement_value: type, is_required: true, display_order: 4 },
      { requirement_name: "Subject Name", requirement_type: "field", requirement_value: "Subject Name", is_required: true, display_order: 5 },
      { requirement_name: "Subject Code", requirement_type: "field", requirement_value: "Subject Code", is_required: true, display_order: 6 },
      { requirement_name: "Branch", requirement_type: "field", requirement_value: "Branch", is_required: true, display_order: 7 },
      { requirement_name: "Department", requirement_type: "field", requirement_value: "Department", is_required: true, display_order: 8 },
      { requirement_name: "Time", requirement_type: "field", requirement_value: "Time", is_required: true, display_order: 9 },
      { requirement_name: "Maximum Marks", requirement_type: "field", requirement_value: "Maximum Marks", is_required: true, display_order: 10 },
      { requirement_name: "Part A", requirement_type: "part a structure", requirement_value: "Part A", is_required: true, display_order: 11 },
      { requirement_name: "Part A Question Count", requirement_type: "question_count", requirement_value: isMid ? "5" : "10", is_required: true, display_order: 12 },
      { requirement_name: "Part A Marks Pattern", requirement_type: "marks", requirement_value: "2 marks", is_required: true, display_order: 13 },
      { requirement_name: "Part A Arrangement", requirement_type: "arrangement", requirement_value: "Part A followed by questions", is_required: true, display_order: 14 },
      { requirement_name: "Part B", requirement_type: "part b structure", requirement_value: "Part B", is_required: true, display_order: 15 },
      { requirement_name: "Part B Question Count", requirement_type: "question_count", requirement_value: isMid ? "6" : "10", is_required: true, display_order: 16 },
      { requirement_name: "Part B Marks Pattern", requirement_type: "marks", requirement_value: "10 marks", is_required: true, display_order: 17 },
      { requirement_name: "Part B Arrangement", requirement_type: "arrangement", requirement_value: "Part B arrangement", is_required: true, display_order: 18 },
      { requirement_name: "Body", requirement_type: "section", requirement_value: "Question Paper Body", is_required: true, display_order: 19 },
      { requirement_name: "Footer", requirement_type: "footer", requirement_value: "Footer section", is_required: true, display_order: 20 },
    ]);
  };

  const addRequirement = () => {
    setRequirements([
      ...requirements,
      {
        requirement_name: "",
        requirement_type: "text",
        requirement_value: "",
        is_required: true,
        display_order: requirements.length + 1,
      },
    ]);
  };

  const updateRequirement = (index, key, val) => {
    const updated = [...requirements];
    updated[index][key] = val;
    setRequirements(updated);
  };

  const removeRequirement = (index) => {
    const updated = requirements.filter((_, i) => i !== index);
    setRequirements(updated.map((item, idx) => ({ ...item, display_order: idx + 1 })));
  };

  const handleSaveFormat = async (e) => {
    e.preventDefault();
    setFeedback({ error: "", success: "" });

    if (!formatName.trim()) {
      setFeedback({ error: "Please enter a Format Name.", success: "" });
      return;
    }

    const validReqs = requirements.filter((r) => r.requirement_name.trim());
    if (validReqs.length === 0) {
      setFeedback({ error: "Please configure at least one structural requirement.", success: "" });
      return;
    }

    setLoading(true);
    try {
      await api.post("/formats", {
        institution_id: user.institution_id,
        department_id: selectedDeptId ? Number(selectedDeptId) : null,
        document_type_id: Number(selectedDocTypeId),
        format_name: formatName.trim(),
        instructions: instructions.trim(),
        requirements: validReqs,
      });

      setFeedback({ error: "", success: "Structural format created and activated successfully!" });
      loadFormats();
      loadDashboardData();
      setActiveTab("formats");
    } catch (err) {
      setFeedback({ error: err.response?.data?.detail || "Failed to save structural format.", success: "" });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFormat = async (formatId) => {
    if (!window.confirm("Are you sure you want to delete this structural format?")) return;
    try {
      await api.delete(`/formats/${formatId}`);
      loadFormats();
      loadDashboardData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete format.");
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

  return (
    <div className="main-content">
      <div className="tab-nav">
        <button
          className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          📊 Overview & Stats
        </button>
        <button
          className={`tab-btn ${activeTab === "builder" ? "active" : ""}`}
          onClick={() => setActiveTab("builder")}
        >
          ⚙️ Format Builder
        </button>
        <button
          className={`tab-btn ${activeTab === "formats" ? "active" : ""}`}
          onClick={() => setActiveTab("formats")}
        >
          📑 Master Formats ({formats.length})
        </button>
        <button
          className={`tab-btn ${activeTab === "submissions" ? "active" : ""}`}
          onClick={() => setActiveTab("submissions")}
        >
          📄 Submitted Documents
        </button>
        <button
          className={`tab-btn ${activeTab === "accepted" ? "active" : ""}`}
          onClick={() => setActiveTab("accepted")}
        >
          ✓ Accepted PDFs
        </button>
      </div>

      {feedback.error && <div className="alert-message alert-danger">⚠️ {feedback.error}</div>}
      {feedback.success && <div className="alert-message alert-success">✓ {feedback.success}</div>}

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && stats && (
        <div>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">Total Submissions</span>
              <span className="stat-value">{stats.total_documents}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Strictly Accepted</span>
              <span className="stat-value accepted">{stats.accepted_documents}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Strictly Rejected</span>
              <span className="stat-value rejected">{stats.rejected_documents}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Pending Analysis</span>
              <span className="stat-value pending">{stats.pending_documents}</span>
            </div>
          </div>

          <div className="panel">
            <div className="panel-header">
              <h3>Recent Institutional Document Submissions</h3>
              <button className="btn btn-secondary btn-sm" onClick={loadDashboardData}>
                ↻ Refresh
              </button>
            </div>

            {recentSubmissions.length === 0 ? (
              <p className="empty-state">No document submissions recorded yet.</p>
            ) : (
              <div className="table-wrapper">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Type</th>
                      <th>Department</th>
                      <th>Uploaded By</th>
                      <th>Date</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentSubmissions.map((doc) => (
                      <tr key={doc.id}>
                        <td><strong>{doc.file_name}</strong></td>
                        <td>{doc.document_type_name || "-"}</td>
                        <td>{doc.department_code || doc.department_name || "Institution"}</td>
                        <td>{doc.uploaded_by_name || "Faculty"}</td>
                        <td>{new Date(doc.uploaded_at).toLocaleDateString()}</td>
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
        </div>
      )}

      {/* TAB 2: FORMAT BUILDER */}
      {activeTab === "builder" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Structural Format Builder</h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Define structural rules without code. Documents uploaded by Faculty are strictly validated against these rules.
              </p>
            </div>
          </div>

          <form onSubmit={handleSaveFormat}>
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
                <label>Department Scope (Optional)</label>
                <select
                  className="form-select"
                  value={selectedDeptId}
                  onChange={(e) => setSelectedDeptId(e.target.value)}
                >
                  <option value="">All Departments (Institution-Wide)</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.code} - {d.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {selectedDocTypeName === "Question Paper" && (
              <div className="form-group">
                <label>Examination Pattern</label>
                <select
                  className="form-select"
                  value={examType}
                  onChange={(e) => {
                    setExamType(e.target.value);
                    applyQuestionPaperPreset(e.target.value);
                  }}
                >
                  <option value="Mid Examination">Mid Examination (Part A: 5x2M, Part B: 6x10M)</option>
                  <option value="Semester Examination">Semester Examination (Part A: 10x2M, Part B: 10x10M)</option>
                </select>
              </div>
            )}

            {/* Quick Presets Bar */}
            <div className="preset-bar">
              <span className="preset-title">⚡ Quick Standard Templates:</span>
              {selectedDocTypeName === "Course Structure" && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={applyCourseStructurePreset}
                >
                  Load Course Structure Standard Template
                </button>
              )}
              {selectedDocTypeName === "Question Bank" && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={applyQuestionBankPreset}
                >
                  Load Question Bank Standard Template (Units 1-5, Part A & B)
                </button>
              )}
              {selectedDocTypeName === "Question Paper" && (
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => applyQuestionPaperPreset(examType)}
                >
                  Load {examType} Standard Template
                </button>
              )}
            </div>

            <div className="form-group">
              <label>Format Name *</label>
              <input
                type="text"
                className="form-input"
                value={formatName}
                onChange={(e) => setFormatName(e.target.value)}
                placeholder="e.g. Standard B.Tech Question Paper Format"
                required
              />
            </div>

            <div className="form-group">
              <label>Auditor Instructions (Optional)</label>
              <textarea
                className="form-textarea"
                rows={2}
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Guidelines or requirements notes for faculty..."
              />
            </div>

            <div style={{ marginTop: "24px", marginBottom: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h4 style={{ fontSize: "15px", fontWeight: "700" }}>Structural Requirements ({requirements.length})</h4>
              <button type="button" className="btn btn-secondary btn-sm" onClick={addRequirement}>
                + Add Requirement
              </button>
            </div>

            <div style={{ marginBottom: "20px" }}>
              {requirements.map((req, idx) => (
                <div key={idx} className="requirement-row">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Requirement Name (e.g. College Header, Part A)"
                    value={req.requirement_name}
                    onChange={(e) => updateRequirement(idx, "requirement_name", e.target.value)}
                    required
                  />

                  <select
                    className="form-select"
                    value={req.requirement_type}
                    onChange={(e) => updateRequirement(idx, "requirement_type", e.target.value)}
                  >
                    <option value="text">Text presence</option>
                    <option value="heading">Heading presence</option>
                    <option value="section">Section presence</option>
                    <option value="field">Field presence</option>
                    <option value="question_count">Required count</option>
                    <option value="marks">Marks pattern</option>
                    <option value="header">Page/header presence</option>
                    <option value="footer">Footer presence</option>
                    <option value="arrangement">Ordering requirement</option>
                    <option value="part a structure">Part A structure</option>
                    <option value="part b structure">Part B structure</option>
                    <option value="custom_rule">Custom structural rule</option>
                  </select>

                  <input
                    type="text"
                    className="form-input"
                    placeholder="Value / Expected pattern (e.g. 5, 2 marks, B.Tech)"
                    value={req.requirement_value}
                    onChange={(e) => updateRequirement(idx, "requirement_value", e.target.value)}
                  />

                  <label style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "12px", cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={req.is_required}
                      onChange={(e) => updateRequirement(idx, "is_required", e.target.checked)}
                    />
                    Required
                  </label>

                  <button
                    type="button"
                    className="btn btn-danger btn-sm"
                    style={{ padding: "6px" }}
                    onClick={() => removeRequirement(idx)}
                    title="Remove"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Saving Format..." : "💾 Save Structural Format"}
            </button>
          </form>
        </div>
      )}

      {/* TAB 3: FORMATS LIST */}
      {activeTab === "formats" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Defined Structural Formats</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Active templates: {formats.length}
              </span>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => setActiveTab("builder")}>
              + Create New Format
            </button>
          </div>

          {formats.length > 0 && (
            <div className="dashboard-toolbar">
              <div className="toolbar-controls">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search format name, document type, department..."
                    value={formatSearchQuery}
                    onChange={(e) => setFormatSearchQuery(e.target.value)}
                  />
                </div>
                {formatSearchQuery && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setFormatSearchQuery("")}
                    title="Clear search"
                  >
                    ✕ Reset
                  </button>
                )}
              </div>
              <span className="toolbar-count">
                Showing{" "}
                {
                  formats.filter((fmt) => {
                    const q = formatSearchQuery.toLowerCase();
                    return (
                      !q ||
                      fmt.format_name.toLowerCase().includes(q) ||
                      (fmt.document_type_name && fmt.document_type_name.toLowerCase().includes(q)) ||
                      (fmt.department_code && fmt.department_code.toLowerCase().includes(q))
                    );
                  }).length
                }{" "}
                of {formats.length}
              </span>
            </div>
          )}

          {formats.length === 0 ? (
            <p className="empty-state">No structural formats defined yet. Click 'Create New Format' to build one.</p>
          ) : (
            (() => {
              const filteredFormats = formats.filter((fmt) => {
                const q = formatSearchQuery.toLowerCase();
                return (
                  !q ||
                  fmt.format_name.toLowerCase().includes(q) ||
                  (fmt.document_type_name && fmt.document_type_name.toLowerCase().includes(q)) ||
                  (fmt.department_code && fmt.department_code.toLowerCase().includes(q))
                );
              });

              if (filteredFormats.length === 0) {
                return <p className="empty-state">No structural formats match your search criteria.</p>;
              }

              return (
                <div className="table-wrapper">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Format Name</th>
                        <th>Document Type</th>
                        <th>Department</th>
                        <th>Rules Count</th>
                        <th>Created At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredFormats.map((fmt) => (
                        <tr key={fmt.id}>
                          <td><strong>{fmt.format_name}</strong></td>
                          <td>{fmt.document_type_name}</td>
                          <td>
                            <span className="branch-pill">
                              {fmt.department_code || "Institution-Wide"}
                            </span>
                          </td>
                          <td>{fmt.requirements?.length || 0} rules</td>
                          <td>{new Date(fmt.created_at).toLocaleDateString()}</td>
                          <td>
                            <div className="table-actions">
                              <button
                                className="btn btn-danger btn-sm"
                                onClick={() => handleDeleteFormat(fmt.id)}
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

      {/* TAB 4: SUBMITTED DOCUMENTS */}
      {activeTab === "submissions" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>All Institutional Submitted Documents</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Total submissions across all branches: {recentSubmissions.length}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadDashboardData}>
              ↻ Refresh
            </button>
          </div>

          {/* Submissions Search & Filters Toolbar */}
          {recentSubmissions.length > 0 && (
            <div className="dashboard-toolbar">
              <div className="toolbar-controls">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search document, type, faculty..."
                    value={subSearchQuery}
                    onChange={(e) => setSubSearchQuery(e.target.value)}
                  />
                </div>

                <select
                  className="toolbar-filter-select"
                  value={subStatusFilter}
                  onChange={(e) => setSubStatusFilter(e.target.value)}
                >
                  <option value="ALL">All Decisions</option>
                  <option value="ACCEPTED">✓ Accepted</option>
                  <option value="REJECTED">✕ Rejected</option>
                  <option value="PENDING">⏳ Pending</option>
                </select>

                <select
                  className="toolbar-filter-select"
                  value={subDeptFilter}
                  onChange={(e) => setSubDeptFilter(e.target.value)}
                >
                  <option value="ALL">All Branches</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.code}>
                      {d.code} ({d.name})
                    </option>
                  ))}
                </select>

                {(subSearchQuery || subStatusFilter !== "ALL" || subDeptFilter !== "ALL") && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setSubSearchQuery("");
                      setSubStatusFilter("ALL");
                      setSubDeptFilter("ALL");
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
                  recentSubmissions.filter((doc) => {
                    const q = subSearchQuery.toLowerCase();
                    const matchesSearch =
                      !q ||
                      doc.file_name.toLowerCase().includes(q) ||
                      (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                      (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q));
                    const matchesStatus =
                      subStatusFilter === "ALL" ||
                      doc.analysis_status === subStatusFilter ||
                      (subStatusFilter === "PENDING" && (!doc.analysis_status || doc.analysis_status === "PENDING"));
                    const matchesDept =
                      subDeptFilter === "ALL" ||
                      doc.department_code === subDeptFilter;
                    return matchesSearch && matchesStatus && matchesDept;
                  }).length
                }{" "}
                of {recentSubmissions.length}
              </span>
            </div>
          )}

          {recentSubmissions.length === 0 ? (
            <p className="empty-state">No submissions available.</p>
          ) : (
            (() => {
              const filtered = recentSubmissions.filter((doc) => {
                const q = subSearchQuery.toLowerCase();
                const matchesSearch =
                  !q ||
                  doc.file_name.toLowerCase().includes(q) ||
                  (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                  (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q));
                const matchesStatus =
                  subStatusFilter === "ALL" ||
                  doc.analysis_status === subStatusFilter ||
                  (subStatusFilter === "PENDING" && (!doc.analysis_status || doc.analysis_status === "PENDING"));
                const matchesDept =
                  subDeptFilter === "ALL" ||
                  doc.department_code === subDeptFilter;
                return matchesSearch && matchesStatus && matchesDept;
              });

              if (filtered.length === 0) {
                return <p className="empty-state">No documents match the specified search or filter criteria.</p>;
              }

              return (
                <div className="table-wrapper">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Document Name</th>
                        <th>Type</th>
                        <th>Branch</th>
                        <th>Uploaded By</th>
                        <th>Uploaded At</th>
                        <th>Decision</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map((doc) => (
                        <tr key={doc.id}>
                          <td><strong>{doc.file_name}</strong></td>
                          <td>{doc.document_type_name}</td>
                          <td>
                            <span className="branch-pill">
                              {doc.department_code || doc.department_name || "Institution"}
                            </span>
                          </td>
                          <td>{doc.uploaded_by_name}</td>
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

      {/* TAB 5: ACCEPTED DOCUMENTS */}
      {activeTab === "accepted" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Verified & Accepted Official Documents</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Auditor-approved documents: {recentSubmissions.filter((d) => d.analysis_status === "ACCEPTED").length}
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadDashboardData}>
              ↻ Refresh
            </button>
          </div>

          {recentSubmissions.filter((d) => d.analysis_status === "ACCEPTED").length > 0 && (
            <div className="dashboard-toolbar">
              <div className="toolbar-controls">
                <div className="search-input-wrapper">
                  <span className="search-icon">🔍</span>
                  <input
                    type="text"
                    className="search-input"
                    placeholder="Search verified file, type, submitter..."
                    value={subSearchQuery}
                    onChange={(e) => setSubSearchQuery(e.target.value)}
                  />
                </div>

                <select
                  className="toolbar-filter-select"
                  value={subDeptFilter}
                  onChange={(e) => setSubDeptFilter(e.target.value)}
                >
                  <option value="ALL">All Branches</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.code}>
                      {d.code} ({d.name})
                    </option>
                  ))}
                </select>

                {(subSearchQuery || subDeptFilter !== "ALL") && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setSubSearchQuery("");
                      setSubDeptFilter("ALL");
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
                  recentSubmissions
                    .filter((d) => d.analysis_status === "ACCEPTED")
                    .filter((doc) => {
                      const q = subSearchQuery.toLowerCase();
                      const matchesSearch =
                        !q ||
                        doc.file_name.toLowerCase().includes(q) ||
                        (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                        (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q));
                      const matchesDept =
                        subDeptFilter === "ALL" ||
                        doc.department_code === subDeptFilter;
                      return matchesSearch && matchesDept;
                    }).length
                }{" "}
                of {recentSubmissions.filter((d) => d.analysis_status === "ACCEPTED").length}
              </span>
            </div>
          )}

          {recentSubmissions.filter((d) => d.analysis_status === "ACCEPTED").length === 0 ? (
            <p className="empty-state">No documents have reached ACCEPTED status yet.</p>
          ) : (
            (() => {
              const filtered = recentSubmissions
                .filter((d) => d.analysis_status === "ACCEPTED")
                .filter((doc) => {
                  const q = subSearchQuery.toLowerCase();
                  const matchesSearch =
                    !q ||
                    doc.file_name.toLowerCase().includes(q) ||
                    (doc.document_type_name && doc.document_type_name.toLowerCase().includes(q)) ||
                    (doc.uploaded_by_name && doc.uploaded_by_name.toLowerCase().includes(q));
                  const matchesDept =
                    subDeptFilter === "ALL" ||
                    doc.department_code === subDeptFilter;
                  return matchesSearch && matchesDept;
                });

              if (filtered.length === 0) {
                return <p className="empty-state">No verified documents match the specified search or filter criteria.</p>;
              }

              return (
                <div className="table-wrapper">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Document Name</th>
                        <th>Type</th>
                        <th>Branch</th>
                        <th>Uploaded By</th>
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
                          <td>
                            <span className="branch-pill">
                              {doc.department_code || doc.department_name}
                            </span>
                          </td>
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

      {/* Comparison Results Modal */}
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

export default AuditorDashboard;
