import React, { useState, useEffect } from "react";
import api from "../api";
import PdfViewerModal from "../components/PdfViewerModal";
import ValidationReportModal from "../components/ValidationReportModal";

function QuestionPaperManagement({ user }) {
  const [loading, setLoading] = useState(false);
  const [dataRows, setDataRows] = useState([]);
  const [filterOptions, setFilterOptions] = useState({
    academic_years: [],
    semesters: [],
    departments: [],
    exam_categories: [],
  });

  // Filters
  const [selectedYear, setSelectedYear] = useState("");
  const [selectedSemester, setSelectedSemester] = useState("");
  const [selectedDept, setSelectedDept] = useState(
    user.role === "HOD" && user.department_id ? String(user.department_id) : ""
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL"); // ALL | COMPLIANT | NON_COMPLIANT

  // Modals state
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [reportModalData, setReportModalData] = useState({ id: null, name: "" });

  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadTarget, setUploadTarget] = useState(null); // { course_id, course_code, course_name, exam_category, existing_doc }
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadFeedback, setUploadFeedback] = useState({ error: "", success: "" });

  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [decisionTarget, setDecisionTarget] = useState(null); // { document_id, file_name, course_name, category }
  const [decisionChoice, setDecisionChoice] = useState("ACCEPTED");
  const [decisionComments, setDecisionComments] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [decisionFeedback, setDecisionFeedback] = useState({ error: "", success: "" });

  useEffect(() => {
    loadFilters();
  }, []);

  useEffect(() => {
    loadOverview();
  }, [selectedYear, selectedSemester, selectedDept, searchQuery]);

  const loadFilters = async () => {
    try {
      const res = await api.get("/question-papers/filters");
      setFilterOptions(res.data);
      // Keep selectedYear empty by default so All Courses display immediately
    } catch (err) {
      console.error("Failed to load question paper filters:", err);
    }
  };

  const loadOverview = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedYear) params.academic_year_id = selectedYear;
      if (selectedSemester) params.semester_id = selectedSemester;
      if (selectedDept) params.department_id = selectedDept;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await api.get("/question-papers/overview", { params });
      setDataRows(res.data.rows || []);
    } catch (err) {
      console.error("Failed to load question paper overview:", err);
    } finally {
      setLoading(false);
    }
  };

  // Open Upload / Replace Modal
  const openUploadModal = (course, examCategory, existingDoc = null) => {
    setUploadTarget({
      course_id: course.course_id,
      course_code: course.course_code,
      course_name: course.course_name,
      department_code: course.department,
      exam_category: examCategory,
      existing_doc: existingDoc,
    });
    setUploadFile(null);
    setUploadFeedback({ error: "", success: "" });
    setUploadModalOpen(true);
  };

  // Handle Upload Submission
  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadFeedback({ error: "Please select a PDF question paper file to upload.", success: "" });
      return;
    }
    if (!uploadFile.name.toLowerCase().endsWith(".pdf")) {
      setUploadFeedback({ error: "Only PDF documents (.pdf) are permitted.", success: "" });
      return;
    }

    setUploading(true);
    setUploadFeedback({ error: "", success: "" });

    const formData = new FormData();
    formData.append("course_id", uploadTarget.course_id);
    formData.append("exam_category", uploadTarget.exam_category);
    formData.append("file", uploadFile);

    try {
      const res = await api.post("/question-papers/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setUploadFeedback({
        error: "",
        success: `File uploaded successfully! Automated Status: ${res.data.validation_status} (${res.data.compliance_percentage}% Compliance).`,
      });

      await loadOverview();
      setTimeout(() => {
        setUploadModalOpen(false);
        // Automatically open the detailed validation report modal to show the results
        if (res.data.document_id) {
          openReportModal(res.data.document_id, uploadFile.name);
        }
      }, 900);
    } catch (err) {
      setUploadFeedback({
        error: err.response?.data?.detail || "Upload failed. Please ensure file is a valid PDF.",
        success: "",
      });
    } finally {
      setUploading(false);
    }
  };

  // Open Decision Modal (HOD, Auditor, Admin)
  const openDecisionModal = (doc, course, categoryLabel) => {
    setDecisionTarget({
      document_id: doc.id,
      file_name: doc.file_name,
      course_name: `${course.course_code} - ${course.course_name}`,
      category: categoryLabel,
      current_status: doc.approval_status,
    });
    setDecisionChoice(doc.approval_status === "PENDING" ? "ACCEPTED" : doc.approval_status);
    setDecisionComments(doc.approval_comments || "");
    setDecisionFeedback({ error: "", success: "" });
    setDecisionModalOpen(true);
  };

  // Handle Decision Submission
  const handleDecisionSubmit = async (e) => {
    e.preventDefault();
    setSubmittingDecision(true);
    setDecisionFeedback({ error: "", success: "" });

    try {
      await api.post(`/question-papers/${decisionTarget.document_id}/decision`, {
        decision: decisionChoice,
        comments: decisionComments,
      });

      setDecisionFeedback({
        error: "",
        success: `Official decision recorded as ${decisionChoice}.`,
      });

      await loadOverview();
      setTimeout(() => {
        setDecisionModalOpen(false);
      }, 700);
    } catch (err) {
      setDecisionFeedback({
        error: err.response?.data?.detail || "Failed to submit decision.",
        success: "",
      });
    } finally {
      setSubmittingDecision(false);
    }
  };

  // Open PDF Viewer Modal
  const openPdfViewer = (doc) => {
    const isAccepted = (doc.approval_status || "").toUpperCase() === "ACCEPTED";
    setPdfModalData({
      id: doc.id,
      name: doc.file_name,
      isAccepted: isAccepted,
    });
    setPdfModalOpen(true);
  };

  // Open 6-Column Validation Report Modal
  const openReportModal = (docId, fileName) => {
    setReportModalData({ id: docId, name: fileName });
    setReportModalOpen(true);
  };

  // Delete uploaded question paper file
  const handleDeletePaper = async (docId, fileName, categoryLabel) => {
    const ok = window.confirm(
      `Are you sure you want to delete the uploaded ${categoryLabel} file:\n"${fileName}"?\n\nThis will remove the file and reset the upload status.`
    );
    if (!ok) return;

    try {
      await api.delete(`/question-papers/documents/${docId}`);
      alert(`Question paper "${fileName}" deleted successfully.`);
      loadOverview();
    } catch (err) {
      console.error("Delete failed:", err);
      alert(err.response?.data?.detail || "Failed to delete question paper.");
    }
  };

  // Download Accepted PDF strictly through authenticated download endpoint
  const handleDownload = async (docId, fileName) => {
    try {
      const res = await api.get(`/documents/${docId}/download`, { responseType: "blob" });
      const blobUrl = URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = fileName || `Question_Paper_${docId}.pdf`;
      link.click();
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      alert(err.response?.data?.detail || "Download rejected: Only formally accepted documents can be downloaded.");
    }
  };

  // Filter rows
  const filteredRows = dataRows.filter((r) => {
    if (statusFilter === "COMPLIANT") return r.is_fully_compliant;
    if (statusFilter === "NON_COMPLIANT") return !r.is_fully_compliant;
    return true;
  });

  // Calculate summary metrics
  const totalCourses = dataRows.length;
  const compliantCount = dataRows.filter((r) => r.is_fully_compliant).length;
  const nonCompliantCount = totalCourses - compliantCount;
  const institutionalComplianceRate = totalCourses > 0 ? Math.round((compliantCount / totalCourses) * 100) : 0;

  const mid1Count = dataRows.filter((r) => r.mid1_paper).length;
  const mid2Count = dataRows.filter((r) => r.mid2_paper).length;
  const semCount = dataRows.filter((r) => r.sem_paper).length;

  const canReview = ["HOD", "Auditor", "Admin"].includes(user.role);

  // Helper for rendering Question Paper cell (Cols 6, 7, 8)
  const renderPaperCell = (course, paper, categoryKey, categoryLabel) => {
    if (!paper) {
      return (
        <div style={{ padding: "6px 8px", background: "rgba(239, 68, 68, 0.05)", borderRadius: "6px", border: "1px dashed rgba(239, 68, 68, 0.25)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span className="badge badge-warning" style={{ fontSize: "11px", backgroundColor: "#ef4444", color: "#fff", padding: "2px 6px" }}>
              Missing
            </span>
            {course.permissions.can_upload && (
              <button
                className="btn btn-sm btn-primary"
                style={{ fontSize: "11px", padding: "2px 8px" }}
                onClick={() => openUploadModal(course, categoryKey)}
                title={`Upload ${categoryLabel} PDF`}
              >
                + Upload
              </button>
            )}
          </div>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
            Mandatory paper required
          </span>
        </div>
      );
    }

    const isValValid = paper.validation_status === "VALID";
    const isValNeedsReview = paper.validation_status === "NEEDS_REVIEW";
    const isAppAccepted = (paper.approval_status || "").toUpperCase() === "ACCEPTED";
    const isAppRejected = (paper.approval_status || "").toUpperCase() === "REJECTED";

    return (
      <div style={{ padding: "8px 10px", background: "var(--surface)", borderRadius: "6px", border: "1px solid var(--border-color)", fontSize: "12px" }}>
        {/* Filename & Version */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
          <span
            style={{ fontWeight: 600, color: "var(--primary)", cursor: "pointer", textDecoration: "underline", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "130px" }}
            onClick={() => openPdfViewer(paper)}
            title={`Preview ${paper.file_name}`}
          >
            📄 {paper.file_name}
          </span>
          <span className="badge" style={{ fontSize: "10px", background: "rgba(100, 116, 139, 0.2)", color: "#cbd5e1" }}>
            v{paper.version}
          </span>
        </div>

        {/* Validation & Approval Badges */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "4px", marginBottom: "6px" }}>
          <span
            className={`badge ${isValValid ? "badge-success" : isValNeedsReview ? "badge-warning" : "badge-danger"}`}
            style={{ fontSize: "10px", padding: "1px 5px", cursor: "pointer" }}
            onClick={() => openReportModal(paper.id, paper.file_name)}
            title="Click to view 6-column automated validation report"
          >
            {paper.validation_status} ({paper.compliance_percentage}%)
          </span>

          <span
            className={`badge ${isAppAccepted ? "badge-success" : isAppRejected ? "badge-danger" : "badge-neutral"}`}
            style={{ fontSize: "10px", padding: "1px 5px" }}
            title={`Approval decision: ${paper.approval_status}`}
          >
            {paper.approval_status}
          </span>
        </div>

        {/* Action icons bar */}
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          <button
            className="btn btn-sm btn-secondary"
            style={{ fontSize: "11px", padding: "2px 6px" }}
            onClick={() => openPdfViewer(paper)}
            title="Preview PDF document"
          >
            👁️ View
          </button>

          <button
            className="btn btn-sm btn-secondary"
            style={{ fontSize: "11px", padding: "2px 6px" }}
            onClick={() => openReportModal(paper.id, paper.file_name)}
            title="View 6-column automated validation report"
          >
            📊 Report
          </button>

          {course.permissions.can_upload && (
            <button
              className="btn btn-sm btn-secondary"
              style={{ fontSize: "11px", padding: "2px 6px" }}
              onClick={() => openUploadModal(course, categoryKey, paper)}
              title="Replace document with updated version"
            >
              🔄 Replace
            </button>
          )}

          {canReview && (
            <button
              className="btn btn-sm btn-secondary"
              style={{ fontSize: "11px", padding: "2px 6px", color: "#38bdf8" }}
              onClick={() => openDecisionModal(paper, course, categoryLabel)}
              title="Review & submit approval/rejection decision"
            >
              ⚖️ Decision
            </button>
          )}

          {(course.permissions.can_upload || user.role === "Faculty" || user.role === "Admin" || user.role === "HOD") && (
            <button
              className="btn btn-sm btn-danger"
              style={{
                fontSize: "11px",
                padding: "2px 6px",
                color: "#ef4444",
                borderColor: "rgba(239, 68, 68, 0.4)",
                background: "rgba(239, 68, 68, 0.08)",
                cursor: "pointer"
              }}
              onClick={() => handleDeletePaper(paper.id, paper.file_name, categoryLabel)}
              title={`Delete ${paper.file_name}`}
            >
              🗑️ Delete
            </button>
          )}

          {isAppAccepted && (
            <button
              className="btn btn-sm btn-success"
              style={{ fontSize: "11px", padding: "2px 6px" }}
              onClick={() => handleDownload(paper.id, paper.file_name)}
              title="Download accepted official PDF record"
            >
              📥
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="qp-management-page" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* 1. Header & Summary Metrics */}
      <div className="card" style={{ padding: "20px", background: "linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "24px" }}>📝</span>
              <h2 style={{ margin: 0, fontSize: "22px", color: "#f8fafc" }}>
                Question Paper Compliance Management
              </h2>
            </div>
            <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "13px" }}>
              Multi-examination question paper verification, automated PDF structural checking, and institutional approval workflows.
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            <button className="btn btn-secondary" onClick={loadOverview} title="Refresh Table">
              🔄 Refresh
            </button>
          </div>
        </div>

        {/* Institutional Coverage Summary Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "12px", marginTop: "20px" }}>
          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(15, 23, 42, 0.6)" }}>
            <span style={{ fontSize: "11px", color: "#94a3b8", textTransform: "uppercase" }}>Total Courses</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#f8fafc", marginTop: "2px" }}>{totalCourses}</div>
          </div>

          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(34, 197, 94, 0.1)", borderColor: "rgba(34, 197, 94, 0.3)" }}>
            <span style={{ fontSize: "11px", color: "#22c55e", textTransform: "uppercase", fontWeight: 600 }}>Fully Compliant</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#22c55e", marginTop: "2px" }}>{compliantCount}</div>
          </div>

          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(239, 68, 68, 0.1)", borderColor: "rgba(239, 68, 68, 0.3)" }}>
            <span style={{ fontSize: "11px", color: "#ef4444", textTransform: "uppercase", fontWeight: 600 }}>Action Required</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#ef4444", marginTop: "2px" }}>{nonCompliantCount}</div>
          </div>

          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(59, 130, 246, 0.1)", borderColor: "rgba(59, 130, 246, 0.3)" }}>
            <span style={{ fontSize: "11px", color: "#3b82f6", textTransform: "uppercase", fontWeight: 600 }}>Mid-1 Uploads</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#3b82f6", marginTop: "2px" }}>{mid1Count} / {totalCourses}</div>
          </div>

          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(59, 130, 246, 0.1)", borderColor: "rgba(59, 130, 246, 0.3)" }}>
            <span style={{ fontSize: "11px", color: "#3b82f6", textTransform: "uppercase", fontWeight: 600 }}>Mid-2 Uploads</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#3b82f6", marginTop: "2px" }}>{mid2Count} / {totalCourses}</div>
          </div>

          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(168, 85, 247, 0.1)", borderColor: "rgba(168, 85, 247, 0.3)" }}>
            <span style={{ fontSize: "11px", color: "#a855f7", textTransform: "uppercase", fontWeight: 600 }}>Semester Uploads</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#a855f7", marginTop: "2px" }}>{semCount} / {totalCourses}</div>
          </div>

          <div className="card" style={{ padding: "12px", textAlign: "center", background: "rgba(14, 165, 233, 0.1)", borderColor: "rgba(14, 165, 233, 0.3)" }}>
            <span style={{ fontSize: "11px", color: "#0ea5e9", textTransform: "uppercase", fontWeight: 600 }}>Compliance Rate</span>
            <div style={{ fontSize: "22px", fontWeight: 700, color: "#0ea5e9", marginTop: "2px" }}>{institutionalComplianceRate}%</div>
          </div>
        </div>
      </div>

      {/* 2. Filters & Search Bar */}
      <div className="card" style={{ padding: "16px", display: "flex", flexWrap: "wrap", gap: "12px", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center", flex: 1 }}>
          {/* Search */}
          <div style={{ minWidth: "220px", flex: 1 }}>
            <input
              type="text"
              className="form-input"
              placeholder="🔍 Search course code, title, or faculty..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ fontSize: "13px" }}
            />
          </div>

          {/* Academic Year */}
          <select
            className="form-input"
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            style={{ minWidth: "180px", fontSize: "13px" }}
          >
            <option value="">All Academic Years</option>
            {filterOptions.academic_years.map((y) => (
              <option key={y.id} value={y.id}>
                {y.year_name} {y.is_current ? "(Current)" : ""}
              </option>
            ))}
          </select>

          {/* Semester */}
          <select
            className="form-input"
            value={selectedSemester}
            onChange={(e) => setSelectedSemester(e.target.value)}
            style={{ minWidth: "180px", fontSize: "13px" }}
          >
            <option value="">All Semesters</option>
            {filterOptions.semesters.map((s) => (
              <option key={s.id} value={s.id}>
                {s.semester_name}
              </option>
            ))}
          </select>

          {/* Department */}
          <select
            className="form-input"
            value={selectedDept}
            onChange={(e) => setSelectedDept(e.target.value)}
            disabled={user.role === "HOD" && user.department_id}
            style={{ minWidth: "280px", fontSize: "13px" }}
          >
            <option value="">All Departments</option>
            {filterOptions.departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.code})
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter Tabs */}
        <div style={{ display: "flex", gap: "6px" }}>
          <button
            className={`btn btn-sm ${statusFilter === "ALL" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter("ALL")}
          >
            All Courses ({dataRows.length})
          </button>
          <button
            className={`btn btn-sm ${statusFilter === "COMPLIANT" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter("COMPLIANT")}
          >
            ✓ Compliant ({compliantCount})
          </button>
          <button
            className={`btn btn-sm ${statusFilter === "NON_COMPLIANT" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setStatusFilter("NON_COMPLIANT")}
          >
            ⚠️ Action Required ({nonCompliantCount})
          </button>
        </div>
      </div>

      {/* 3. Dedicated 12-Column Table */}
      <div className="card" style={{ padding: "0", overflow: "hidden" }}>
        <div className="table-responsive" style={{ maxHeight: "calc(100vh - 380px)", overflowY: "auto" }}>
          <table className="table" style={{ margin: 0, fontSize: "12px", width: "100%", borderCollapse: "collapse" }}>
            <thead style={{ position: "sticky", top: 0, zIndex: 10, background: "#1e293b", borderBottom: "2px solid var(--border-color)" }}>
              <tr>
                <th style={{ width: "7%", padding: "10px 8px" }}>1. Academic Year</th>
                <th style={{ width: "7%", padding: "10px 8px" }}>2. Semester</th>
                <th style={{ width: "5%", padding: "10px 8px" }}>3. Dept</th>
                <th style={{ width: "13%", padding: "10px 8px" }}>4. Course / Subject</th>
                <th style={{ width: "10%", padding: "10px 8px" }}>5. Faculty Name</th>
                <th style={{ width: "14%", padding: "10px 8px" }}>6. Mid-1 Paper</th>
                <th style={{ width: "14%", padding: "10px 8px" }}>7. Mid-2 Paper</th>
                <th style={{ width: "14%", padding: "10px 8px" }}>8. Semester Paper</th>
                <th style={{ width: "7%", padding: "10px 8px" }}>9. Uploaded Date</th>
                <th style={{ width: "6%", padding: "10px 8px" }}>10. Validation</th>
                <th style={{ width: "6%", padding: "10px 8px" }}>11. Approval</th>
                <th style={{ width: "7%", padding: "10px 8px" }}>12. Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="12" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    <div className="spinner" style={{ width: "28px", height: "28px", margin: "0 auto 8px" }}></div>
                    Loading institutional question paper records...
                  </td>
                </tr>
              ) : filteredRows.length === 0 ? (
                <tr>
                  <td colSpan="12" style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No course examination records match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredRows.map((row) => {
                  const isFullyCompliant = row.is_fully_compliant;

                  return (
                    <tr
                      key={row.course_id}
                      style={{
                        backgroundColor: isFullyCompliant ? "rgba(34, 197, 94, 0.02)" : "transparent",
                        borderBottom: "1px solid var(--border-color)",
                      }}
                    >
                      {/* 1. Academic Year */}
                      <td style={{ padding: "10px 8px", fontWeight: 500 }}>
                        {row.academic_year}
                      </td>

                      {/* 2. Semester */}
                      <td style={{ padding: "10px 8px", color: "#93c5fd" }}>
                        {row.semester}
                      </td>

                      {/* 3. Department */}
                      <td style={{ padding: "10px 8px" }}>
                        <span className="badge badge-neutral" style={{ fontWeight: 600 }}>
                          {row.department}
                        </span>
                      </td>

                      {/* 4. Course / Subject */}
                      <td style={{ padding: "10px 8px" }}>
                        <div style={{ fontWeight: 600, color: "var(--text-main)" }}>
                          {row.course_code}
                        </div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                          {row.course_name}
                        </div>
                      </td>

                      {/* 5. Faculty Name */}
                      <td style={{ padding: "10px 8px" }}>
                        <div style={{ fontWeight: 500, color: row.faculty_name === "Unassigned" ? "#f59e0b" : "var(--text-main)" }}>
                          {row.faculty_name}
                        </div>
                      </td>

                      {/* 6. Mid-1 Question Paper */}
                      <td style={{ padding: "8px 6px" }}>
                        {renderPaperCell(row, row.mid1_paper, "MID1", "Mid-1 Exam")}
                      </td>

                      {/* 7. Mid-2 Question Paper */}
                      <td style={{ padding: "8px 6px" }}>
                        {renderPaperCell(row, row.mid2_paper, "MID2", "Mid-2 Exam")}
                      </td>

                      {/* 8. Semester / End-Semester Question Paper */}
                      <td style={{ padding: "8px 6px" }}>
                        {renderPaperCell(row, row.sem_paper, "SEM", "End Semester Exam")}
                      </td>

                      {/* 9. Uploaded Date */}
                      <td style={{ padding: "10px 8px", fontSize: "11px", color: "var(--text-muted)" }}>
                        {row.uploaded_date}
                      </td>

                      {/* 10. Validation Status */}
                      <td style={{ padding: "10px 8px" }}>
                        <span
                          className={`badge ${
                            row.validation_status === "Valid"
                              ? "badge-success"
                              : row.validation_status === "Missing"
                              ? "badge-danger"
                              : row.validation_status === "Invalid"
                              ? "badge-danger"
                              : "badge-warning"
                          }`}
                          style={{ fontSize: "11px", fontWeight: 600 }}
                        >
                          {row.validation_status}
                        </span>
                      </td>

                      {/* 11. Approval Status */}
                      <td style={{ padding: "10px 8px" }}>
                        <span
                          className={`badge ${
                            row.approval_status === "Accepted"
                              ? "badge-success"
                              : row.approval_status === "Rejected"
                              ? "badge-danger"
                              : "badge-neutral"
                          }`}
                          style={{ fontSize: "11px", fontWeight: 600 }}
                        >
                          {row.approval_status}
                        </span>
                      </td>

                      {/* 12. Actions */}
                      <td style={{ padding: "10px 8px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                          {row.permissions.can_upload && (!row.mid1_paper || !row.mid2_paper || !row.sem_paper) && (
                            <button
                              className="btn btn-sm btn-primary"
                              style={{ fontSize: "11px", padding: "3px 6px" }}
                              onClick={() => {
                                const nextMissing = !row.mid1_paper ? "MID1" : !row.mid2_paper ? "MID2" : "SEM";
                                openUploadModal(row, nextMissing);
                              }}
                            >
                              + Upload
                            </button>
                          )}

                          <button
                            className="btn btn-sm btn-secondary"
                            style={{ fontSize: "11px", padding: "3px 6px" }}
                            onClick={() => {
                              const firstAvailable = row.mid1_paper || row.mid2_paper || row.sem_paper;
                              if (firstAvailable) {
                                openReportModal(firstAvailable.id, firstAvailable.file_name);
                              } else {
                                alert("No question papers have been uploaded yet for this course.");
                              }
                            }}
                          >
                            📊 View
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload / Replace Document Modal */}
      {uploadModalOpen && uploadTarget && (
        <div className="modal-overlay" onClick={() => setUploadModalOpen(false)}>
          <div className="modal-dialog" style={{ maxWidth: "540px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>
                  {uploadTarget.existing_doc ? "Replace Question Paper" : "Upload Question Paper"}
                </h3>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
                  {uploadTarget.course_code} - {uploadTarget.course_name} ({uploadTarget.exam_category})
                </p>
              </div>
              <button className="modal-close-btn" onClick={() => setUploadModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleUploadSubmit}>
              <div className="modal-body">
                {uploadTarget.existing_doc && (
                  <div className="alert alert-warning" style={{ fontSize: "12px", marginBottom: "16px" }}>
                    ⚠️ An existing document <strong>{uploadTarget.existing_doc.file_name} (v{uploadTarget.existing_doc.version})</strong> is currently registered. Uploading a replacement will archive this file into the immutable version retention log and trigger new automated validation checks.
                  </div>
                )}

                {uploadFeedback.error && (
                  <div className="alert alert-danger" style={{ marginBottom: "14px" }}>
                    ⚠️ {uploadFeedback.error}
                  </div>
                )}
                {uploadFeedback.success && (
                  <div className="alert alert-success" style={{ marginBottom: "14px" }}>
                    ✓ {uploadFeedback.success}
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Examination Category</label>
                  <input
                    type="text"
                    className="form-input"
                    value={
                      uploadTarget.exam_category === "MID1"
                        ? "Mid-Semester Examination 1 (MID1 - 30 Marks)"
                        : uploadTarget.exam_category === "MID2"
                        ? "Mid-Semester Examination 2 (MID2 - 30 Marks)"
                        : "End Semester Examination (SEM - 70 Marks)"
                    }
                    disabled
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Select Question Paper (PDF Only)</label>
                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    className="form-input"
                    onChange={(e) => setUploadFile(e.target.files[0] || null)}
                    required
                  />
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                    Strict institutional format: Text-based or OCR-readable PDF, Part A / Part B sections, course code matching {uploadTarget.course_code}.
                  </span>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setUploadModalOpen(false)}
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={uploading || !uploadFile}
                >
                  {uploading ? "Analyzing Structure..." : uploadTarget.existing_doc ? "Upload Replacement" : "Upload & Analyze PDF"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review / Decision Modal (for HOD, Auditor, Admin) */}
      {decisionModalOpen && decisionTarget && (
        <div className="modal-overlay" onClick={() => setDecisionModalOpen(false)}>
          <div className="modal-dialog" style={{ maxWidth: "560px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>Official Audit Review & Decision</h3>
                <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
                  {decisionTarget.course_name} | {decisionTarget.file_name}
                </p>
              </div>
              <button className="modal-close-btn" onClick={() => setDecisionModalOpen(false)}>✕</button>
            </div>

            <form onSubmit={handleDecisionSubmit}>
              <div className="modal-body">
                {decisionFeedback.error && (
                  <div className="alert alert-danger" style={{ marginBottom: "14px" }}>
                    ⚠️ {decisionFeedback.error}
                  </div>
                )}
                {decisionFeedback.success && (
                  <div className="alert alert-success" style={{ marginBottom: "14px" }}>
                    ✓ {decisionFeedback.success}
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Official Compliance Decision</label>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px" }}>
                    <button
                      type="button"
                      className={`btn ${decisionChoice === "ACCEPTED" ? "btn-success" : "btn-secondary"}`}
                      onClick={() => setDecisionChoice("ACCEPTED")}
                      style={{ padding: "10px", fontSize: "13px" }}
                    >
                      ✓ Accept
                    </button>
                    <button
                      type="button"
                      className={`btn ${decisionChoice === "REJECTED" ? "btn-danger" : "btn-secondary"}`}
                      onClick={() => setDecisionChoice("REJECTED")}
                      style={{ padding: "10px", fontSize: "13px" }}
                    >
                      ✕ Reject
                    </button>
                    <button
                      type="button"
                      className={`btn ${decisionChoice === "NEEDS_REVIEW" ? "btn-warning" : "btn-secondary"}`}
                      onClick={() => setDecisionChoice("NEEDS_REVIEW")}
                      style={{ padding: "10px", fontSize: "13px", backgroundColor: decisionChoice === "NEEDS_REVIEW" ? "#8b5cf6" : undefined, color: "#fff" }}
                    >
                      🔍 Flag Review
                    </button>
                  </div>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", display: "block" }}>
                    {decisionChoice === "ACCEPTED" && "Official acceptance unlocks download permissions for institutional records."}
                    {decisionChoice === "REJECTED" && "Faculty will be notified to correct and re-upload an updated revision."}
                    {decisionChoice === "NEEDS_REVIEW" && "Document flagged for manual institutional review or syllabus alignment."}
                  </span>
                </div>

                <div className="form-group">
                  <label className="form-label">Review Findings & Comments</label>
                  <textarea
                    className="form-input"
                    rows="4"
                    value={decisionComments}
                    onChange={(e) => setDecisionComments(e.target.value)}
                    placeholder="Enter formal compliance findings, recommendations, or reason for rejection..."
                    required={decisionChoice === "REJECTED"}
                  ></textarea>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setDecisionModalOpen(false)}
                  disabled={submittingDecision}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submittingDecision}
                >
                  {submittingDecision ? "Recording Decision..." : "Submit Formal Decision"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PDF Viewer Modal */}
      <PdfViewerModal
        isOpen={pdfModalOpen}
        onClose={() => setPdfModalOpen(false)}
        documentId={pdfModalData.id}
        fileName={pdfModalData.name}
        isAccepted={pdfModalData.isAccepted}
        canDownload={canReview}
        onDownload={handleDownload}
      />

      {/* 6-Column Validation Report Modal */}
      <ValidationReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        documentId={reportModalData.id}
        fileName={reportModalData.name}
        onViewPdf={(docId, name) => {
          setPdfModalData({ id: docId, name, isAccepted: false });
          setPdfModalOpen(true);
        }}
      />
    </div>
  );
}

export default QuestionPaperManagement;
