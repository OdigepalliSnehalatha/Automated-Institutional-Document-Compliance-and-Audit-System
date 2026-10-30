import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";
import Format from "../Format";

function AuditorDashboard({ user, activeTab: propActiveTab, onTabChange }) {
  const [internalActiveTab, setInternalActiveTab] = useState("overview"); // overview | builder | formats | submissions | accepted
  const [showAdvancedFormatManager, setShowAdvancedFormatManager] = useState(false);
  const activeTab = propActiveTab || internalActiveTab;
  const setActiveTab = (tab) => {
    setInternalActiveTab(tab);
    if (onTabChange) onTabChange(tab);
  };
  const [stats, setStats] = useState(null);
  const [recentSubmissions, setRecentSubmissions] = useState([]);
  const [formats, setFormats] = useState([]);
  const [documentTypes, setDocumentTypes] = useState([]);
  const [departments, setDepartments] = useState([]);

  // Format Builder State
  const [selectedDocTypeId, setSelectedDocTypeId] = useState("");
  const [examType, setExamType] = useState("Mid Examination");
  const [midSubdivision, setMidSubdivision] = useState("Mid 1");
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
    const csType = documentTypes.find(
      (t) => t.name.toLowerCase().includes("course structure") || t.name.toLowerCase().includes("structure")
    );
    if (csType) setSelectedDocTypeId(String(csType.id));

    setFormatName("Standard Institutional Course Structure Format");
    setInstructions(
      "Course structure format enforcing official college header, course identification, regulations (R-24), course objectives, Units 1-5 syllabus architecture, prescribed textbooks & reference books, and CO1-CO6 course outcomes."
    );
    setRequirements([
      { requirement_name: "College Header", requirement_type: "header", requirement_value: "Anantha Lakshmi Institute of Technology & Sciences", is_required: true, display_order: 1 },
      { requirement_name: "Autonomous Status", requirement_type: "text", requirement_value: "(Autonomous)", is_required: true, display_order: 2 },
      { requirement_name: "Course Code", requirement_type: "text", requirement_value: "Course Code (e.g. 24ALBTCS403T)", is_required: true, display_order: 3 },
      { requirement_name: "Course Name", requirement_type: "heading", requirement_value: "Course Title / Subject Name", is_required: true, display_order: 4 },
      { requirement_name: "Academic Regulations", requirement_type: "text", requirement_value: "Regulations: R-24", is_required: true, display_order: 5 },
      { requirement_name: "Semester & Branch", requirement_type: "heading", requirement_value: "B.Tech Year, Semester, and Branch Details", is_required: true, display_order: 6 },
      { requirement_name: "Course Objectives", requirement_type: "structure", requirement_value: "Course Objectives section with detailed learning goals", is_required: true, display_order: 7 },
      { requirement_name: "Unit 1 (Syllabus)", requirement_type: "structure", requirement_value: "UNIT-I heading with comprehensive syllabus topics", is_required: true, display_order: 8 },
      { requirement_name: "Unit 2 (Syllabus)", requirement_type: "structure", requirement_value: "UNIT-II heading with comprehensive syllabus topics", is_required: true, display_order: 9 },
      { requirement_name: "Unit 3 (Syllabus)", requirement_type: "structure", requirement_value: "UNIT-III heading with comprehensive syllabus topics", is_required: true, display_order: 10 },
      { requirement_name: "Unit 4 (Syllabus)", requirement_type: "structure", requirement_value: "UNIT-IV heading with comprehensive syllabus topics", is_required: true, display_order: 11 },
      { requirement_name: "Unit 5 (Syllabus)", requirement_type: "structure", requirement_value: "UNIT-V heading with comprehensive syllabus topics", is_required: true, display_order: 12 },
      { requirement_name: "Course Outcomes (CO1-CO6)", requirement_type: "structure", requirement_value: "Defined Course Outcomes list (CO1 to CO6)", is_required: true, display_order: 13 },
      { requirement_name: "Text Books & References", requirement_type: "structure", requirement_value: "Prescribed Text Books and Reference Books list", is_required: true, display_order: 14 },
    ]);
    setFeedback({
      success: "✓ Loaded Standard Course Structure requirements (14 rules).",
      error: ""
    });
  };

  const applyQuestionBankPreset = () => {
    const qbType = documentTypes.find((t) => t.name.toLowerCase().includes("bank"));
    if (qbType) setSelectedDocTypeId(String(qbType.id));

    setFormatName("Standard Institutional Question Bank Format (Units 1-5)");
    setInstructions("Question bank requiring College Name, Course Details, Semester, and Units 1-5 with Part A (10 x 2M) and Part B (10 x 10M).");
    const reqs = [
      { requirement_name: "College Header", requirement_type: "header", requirement_value: "Anantha Lakshmi Institute of Technology & Sciences", is_required: true, display_order: 1 },
      { requirement_name: "Autonomous Status", requirement_type: "text", requirement_value: "(Autonomous)", is_required: true, display_order: 2 },
      { requirement_name: "Course Name & Code", requirement_type: "heading", requirement_value: "Course Name and Course Code must be present", is_required: true, display_order: 3 },
      { requirement_name: "Semester & Branch", requirement_type: "heading", requirement_value: "Semester and Branch details", is_required: true, display_order: 4 },
    ];
    let order = 5;
    for (let u = 1; u <= 5; u++) {
      reqs.push({ requirement_name: `Unit ${u}`, requirement_type: "structure", requirement_value: `Unit ${u} heading must be present`, is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part A`, requirement_type: "structure", requirement_value: `Part A must be present under Unit ${u}`, is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part A Question Count`, requirement_type: "question_count", requirement_value: "10", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part A Marks`, requirement_type: "marks", requirement_value: "2 marks per question", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part B`, requirement_type: "structure", requirement_value: `Part B must be present under Unit ${u}`, is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part B Question Count`, requirement_type: "question_count", requirement_value: "10", is_required: true, display_order: order++ });
      reqs.push({ requirement_name: `Unit ${u} Part B Marks`, requirement_type: "marks", requirement_value: "10 marks per question", is_required: true, display_order: order++ });
    }
    setRequirements(reqs);
    setFeedback({
      success: `✓ Loaded Standard Question Bank requirements (${reqs.length} rules).`,
      error: ""
    });
  };

  const applyMid1Preset = () => {
    const midType = documentTypes.find(
      (t) =>
        t.name.toLowerCase().includes("mid 1") ||
        t.name.toLowerCase().includes("mid") ||
        t.name.toLowerCase().includes("evaluation")
    );
    if (midType) setSelectedDocTypeId(String(midType.id));

    setFormatName("Standard I-MID Paper Format (Autonomous R-24 / 40 Marks)");
    setInstructions(
      "I-MID Examination Paper (Autonomous R-24 Format). Requires official header with (Autonomous), location 515721, Subject with Code, Regulations: R-24, Time: 110 Min, Max Marks: 40, Table format with Blooms Level & CO, Question 1 (a-e @ 2M = 10M), and 3 Unit questions (Units 1-3) with internal choice (10M each). Total = 40 Marks."
    );
    setRequirements([
      { requirement_name: "College Header", requirement_type: "header", requirement_value: "Anantha Lakshmi Institute of Technology & Sciences", is_required: true, display_order: 1 },
      { requirement_name: "Autonomous Status", requirement_type: "text", requirement_value: "(Autonomous)", is_required: true, display_order: 2 },
      { requirement_name: "Institutional Location", requirement_type: "text", requirement_value: "Near S.K. University, Ananthapuramu- 515721", is_required: true, display_order: 3 },
      { requirement_name: "Class & Semester", requirement_type: "heading", requirement_value: "B.Tech Semester (e.g., I B.Tech II Semester)", is_required: true, display_order: 4 },
      { requirement_name: "Examination Title", requirement_type: "heading", requirement_value: "I-MID Examinations", is_required: true, display_order: 5 },
      { requirement_name: "Subject with Code", requirement_type: "heading", requirement_value: "Subject with Code: [Subject Name] : [Subject Code]", is_required: true, display_order: 6 },
      { requirement_name: "Branch Identifier", requirement_type: "text", requirement_value: "Branch: Designated engineering branch (CSE, ECE, ME, CE, EEE)", is_required: true, display_order: 7 },
      { requirement_name: "Academic Regulations", requirement_type: "text", requirement_value: "Regulations: R-24", is_required: true, display_order: 8 },
      { requirement_name: "Time Duration", requirement_type: "text", requirement_value: "Time: 110 Min", is_required: true, display_order: 9 },
      { requirement_name: "Maximum Marks", requirement_type: "marks", requirement_value: "Max. Marks: 40", is_required: true, display_order: 10 },
      { requirement_name: "General Instruction", requirement_type: "text", requirement_value: "Answer all questions", is_required: true, display_order: 11 },
      { requirement_name: "Table Column: S.No", requirement_type: "structure", requirement_value: "S.No", is_required: true, display_order: 12 },
      { requirement_name: "Table Column: Blooms Level", requirement_type: "structure", requirement_value: "Blooms Level (e.g. Apply, Remember, Understand, Analyze)", is_required: true, display_order: 13 },
      { requirement_name: "Table Column: Course Outcome", requirement_type: "structure", requirement_value: "Course Outcome (e.g. CO1 to CO6)", is_required: true, display_order: 14 },
      { requirement_name: "Table Column: Marks", requirement_type: "structure", requirement_value: "Marks (e.g. 2, 5, 10)", is_required: true, display_order: 15 },
      { requirement_name: "Short Answer Section", requirement_type: "question_count", requirement_value: "Question 1 with 5 sub-questions (a, b, c, d, e) @ 2 Marks each = 10 Marks", is_required: true, display_order: 16 },
      { requirement_name: "Unit Coverage (Units 1-3)", requirement_type: "structure", requirement_value: "UNIT-I, UNIT-II, and UNIT-III (Part)", is_required: true, display_order: 17 },
      { requirement_name: "Internal Choice (OR)", requirement_type: "structure", requirement_value: "Internal Choice 'OR' between questions under each Unit", is_required: true, display_order: 18 },
      { requirement_name: "Unit Marks Weightage", requirement_type: "marks", requirement_value: "Each Unit carries 10 Marks (either single 10M or subdivided 5M + 5M)", is_required: true, display_order: 19 },
      { requirement_name: "Total Marks Scheme", requirement_type: "marks", requirement_value: "Total 40 Marks (Q1: 10M + 3 Units x 10M = 40 Marks)", is_required: true, display_order: 20 },
    ]);
    setFeedback({
      success: "✓ Loaded Standard I-MID Paper requirements (20 rules) from R-24 PDF standard.",
      error: ""
    });
  };

  const applyMid2Preset = () => {
    const midType = documentTypes.find(
      (t) =>
        t.name.toLowerCase().includes("mid 2") ||
        t.name.toLowerCase().includes("mid") ||
        t.name.toLowerCase().includes("evaluation")
    );
    if (midType) setSelectedDocTypeId(String(midType.id));

    setFormatName("Standard II-MID Paper Format (Autonomous R-24 / 40 Marks)");
    setInstructions(
      "II-MID Examination Paper (Autonomous R-24 Format). Requires official header with (Autonomous), location 515721, Subject with Code, Regulations: R-24, Time: 110 Min, Max Marks: 40, Table format with Blooms Level & CO, Question 1 (a-e @ 2M = 10M), and 3 Unit questions (Units 3-5) with internal choice (10M each). Total = 40 Marks."
    );
    setRequirements([
      { requirement_name: "College Header", requirement_type: "header", requirement_value: "Anantha Lakshmi Institute of Technology & Sciences", is_required: true, display_order: 1 },
      { requirement_name: "Autonomous Status", requirement_type: "text", requirement_value: "(Autonomous)", is_required: true, display_order: 2 },
      { requirement_name: "Institutional Location", requirement_type: "text", requirement_value: "Near S.K. University, Ananthapuramu- 515721", is_required: true, display_order: 3 },
      { requirement_name: "Class & Semester", requirement_type: "heading", requirement_value: "B.Tech Semester (e.g., I B.Tech II Semester)", is_required: true, display_order: 4 },
      { requirement_name: "Examination Title", requirement_type: "heading", requirement_value: "II-MID Examinations", is_required: true, display_order: 5 },
      { requirement_name: "Subject with Code", requirement_type: "heading", requirement_value: "Subject with Code: [Subject Name] : [Subject Code]", is_required: true, display_order: 6 },
      { requirement_name: "Branch Identifier", requirement_type: "text", requirement_value: "Branch: Designated engineering branch (CSE, ECE, ME, CE, EEE)", is_required: true, display_order: 7 },
      { requirement_name: "Academic Regulations", requirement_type: "text", requirement_value: "Regulations: R-24", is_required: true, display_order: 8 },
      { requirement_name: "Time Duration", requirement_type: "text", requirement_value: "Time: 110 Min", is_required: true, display_order: 9 },
      { requirement_name: "Maximum Marks", requirement_type: "marks", requirement_value: "Max. Marks: 40", is_required: true, display_order: 10 },
      { requirement_name: "General Instruction", requirement_type: "text", requirement_value: "Answer all questions", is_required: true, display_order: 11 },
      { requirement_name: "Table Column: S.No", requirement_type: "structure", requirement_value: "S.No", is_required: true, display_order: 12 },
      { requirement_name: "Table Column: Blooms Level", requirement_type: "structure", requirement_value: "Blooms Level (e.g. Apply, Remember, Understand, Analyze)", is_required: true, display_order: 13 },
      { requirement_name: "Table Column: Course Outcome", requirement_type: "structure", requirement_value: "Course Outcome (e.g. CO1 to CO6)", is_required: true, display_order: 14 },
      { requirement_name: "Table Column: Marks", requirement_type: "structure", requirement_value: "Marks (e.g. 2, 5, 10)", is_required: true, display_order: 15 },
      { requirement_name: "Short Answer Section", requirement_type: "question_count", requirement_value: "Question 1 with 5 sub-questions (a, b, c, d, e) @ 2 Marks each = 10 Marks", is_required: true, display_order: 16 },
      { requirement_name: "Unit Coverage (Units 3-5)", requirement_type: "structure", requirement_value: "UNIT-III (Part), UNIT-IV, and UNIT-V", is_required: true, display_order: 17 },
      { requirement_name: "Internal Choice (OR)", requirement_type: "structure", requirement_value: "Internal Choice 'OR' between questions under each Unit", is_required: true, display_order: 18 },
      { requirement_name: "Unit Marks Weightage", requirement_type: "marks", requirement_value: "Each Unit carries 10 Marks (either single 10M or subdivided 5M + 5M)", is_required: true, display_order: 19 },
      { requirement_name: "Total Marks Scheme", requirement_type: "marks", requirement_value: "Total 40 Marks (Q1: 10M + 3 Units x 10M = 40 Marks)", is_required: true, display_order: 20 },
    ]);
    setFeedback({
      success: "✓ Loaded Standard II-MID Paper requirements (20 rules) from R-24 PDF standard.",
      error: ""
    });
  };

  const applySemesterPaperPreset = () => {
    const semType = documentTypes.find(
      (t) =>
        t.name.toLowerCase().includes("semester") ||
        t.name.toLowerCase().includes("evaluation")
    );
    if (semType) setSelectedDocTypeId(String(semType.id));

    setFormatName("Standard Semester Examination Paper Format (R-24 / 70 Marks)");
    setInstructions(
      "Autonomous R-24 Semester Examination Paper format matching official ALITS template. Requires Hall Ticket Number box (H.T.No), Course Code, Regulations R24, College Header, (Autonomous), B.Tech Year & Semester, Subject Name, Branch/Department, Time: 3 Hours, SET-1, Max. Marks: 70, General Instructions (10 Part-A questions @ 2M, 1 Part-B question per unit @ 10M), Table format with S.No, Question statement, Marks (M), Course Outcome (CO1-CO6), and Bloom's Level (L1/L2), PART-A (10 x 2M = 20M), and PART-B (5 Units with internal choice 'OR' @ 10M = 50M). Grand Total = 70 Marks."
    );
    setRequirements([
      { requirement_name: "College Header", requirement_type: "header", requirement_value: "Anantha Lakshmi Institute of Technology & Sciences", is_required: true, display_order: 1 },
      { requirement_name: "Autonomous Status", requirement_type: "text", requirement_value: "(Autonomous)", is_required: true, display_order: 2 },
      { requirement_name: "Course Code", requirement_type: "text", requirement_value: "Course Code (e.g. 24ALBTCS403T)", is_required: true, display_order: 3 },
      { requirement_name: "Hall Ticket Number Box", requirement_type: "structure", requirement_value: "H.T.No: 10-cell student roll number box", is_required: true, display_order: 4 },
      { requirement_name: "Academic Regulations", requirement_type: "text", requirement_value: "Regulations: R24 / R-24", is_required: true, display_order: 5 },
      { requirement_name: "Class & Semester", requirement_type: "heading", requirement_value: "B.Tech [Year] Year [Semester] Semester Regular/Supplementary Examinations", is_required: true, display_order: 6 },
      { requirement_name: "Subject Name", requirement_type: "heading", requirement_value: "Subject Name (e.g. SOFTWARE ENGINEERING)", is_required: true, display_order: 7 },
      { requirement_name: "Branch / Department", requirement_type: "heading", requirement_value: "Branch / Department (e.g. COMPUTER SCIENCE AND ENGINEERING)", is_required: true, display_order: 8 },
      { requirement_name: "Time Duration", requirement_type: "text", requirement_value: "Time: 3 Hours", is_required: true, display_order: 9 },
      { requirement_name: "Paper Set Identifier", requirement_type: "text", requirement_value: "SET-1 / SET-2 / SET-3 / SET-4", is_required: true, display_order: 10 },
      { requirement_name: "Maximum Marks", requirement_type: "marks", requirement_value: "Max. Marks: 70", is_required: true, display_order: 11 },
      { requirement_name: "General Instructions", requirement_type: "text", requirement_value: "Instructions: 1. Answer all 10 questions from Part-A (2 marks each). 2. Answer one full question from each unit in Part-B (10 marks each).", is_required: true, display_order: 12 },
      { requirement_name: "Table Format Columns", requirement_type: "structure", requirement_value: "Table format with S.No, Question statement, Marks (M), Course Outcome (CO1-CO6), and Bloom's Level (L1/L2)", is_required: true, display_order: 13 },
      { requirement_name: "PART-A Section", requirement_type: "structure", requirement_value: "PART-A heading (Short Answer Section, Questions 1.a through 1.j)", is_required: true, display_order: 14 },
      { requirement_name: "PART-A Questions (10 x 2M)", requirement_type: "question_count", requirement_value: "10 Sub-questions (a, b, c, d, e, f, g, h, i, j) @ 2 Marks each = 20 Marks", is_required: true, display_order: 15 },
      { requirement_name: "PART-A CO & Bloom's Mapping", requirement_type: "structure", requirement_value: "Course Outcomes (CO1 to CO6) and Bloom's Level (L1/L2) mapped for all 10 Part-A sub-questions", is_required: true, display_order: 16 },
      { requirement_name: "PART-B Section", requirement_type: "structure", requirement_value: "PART-B heading (Descriptive Unit-wise Questions)", is_required: true, display_order: 17 },
      { requirement_name: "Unit Coverage (Units I - V)", requirement_type: "structure", requirement_value: "5 Units clearly demarcated: UNIT-I, UNIT-II, UNIT-III, UNIT-IV, and UNIT-V", is_required: true, display_order: 18 },
      { requirement_name: "Internal Choice (OR)", requirement_type: "structure", requirement_value: "Internal Choice 'OR' between questions in each Unit (Q2/Q3, Q4/Q5, Q6/Q7, Q8/Q9, Q10/Q11)", is_required: true, display_order: 19 },
      { requirement_name: "Unit Marks Weightage (5 x 10M)", requirement_type: "marks", requirement_value: "Each Unit carries 10 Marks with CO and Bloom's Level = 50 Marks", is_required: true, display_order: 20 },
      { requirement_name: "Total Marks Scheme Verification", requirement_type: "marks", requirement_value: "Total 70 Marks (Part-A: 20M + Part-B: 50M = 70 Marks)", is_required: true, display_order: 21 },
    ]);
    setFeedback({
      success: "✓ Loaded Standard Semester Examination Paper requirements (21 rules) from R-24 PDF standard.",
      error: ""
    });
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

      {/* ADVANCED FORMAT & COMPARISON SUITE VIEW */}
      {showAdvancedFormatManager ? (
        <Format onBack={() => setShowAdvancedFormatManager(false)} />
      ) : (
        <>
      {/* TAB 2: FORMAT BUILDER */}
      {activeTab === "builder" && (
        <div className="panel">
          <div className="panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3>Structural Format Builder</h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Define structural rules without code. Documents uploaded by Faculty are strictly validated against these rules.
              </p>
            </div>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => setShowAdvancedFormatManager(true)}
            >
              🔍 Open Advanced Format & Comparison Suite →
            </button>
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
                  {documentTypes
                    .filter((t) => t.is_active !== false)
                    .map((t) => {
                      const cleanName = t.name
                        .replace(/Question Paper/gi, "Paper")
                        .replace(/Question Papers/gi, "Papers")
                        .trim();
                      return (
                        <option key={t.id} value={t.id}>
                          {cleanName}
                        </option>
                      );
                    })}
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

            {/* Quick Presets Bar with all 4 Standard Requirements */}
            <div className="preset-bar" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px", margin: "16px 0", padding: "14px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
              <span className="preset-title" style={{ fontWeight: 700, fontSize: "13px", color: "#1e293b", marginRight: "4px" }}>
                ⚡ Quick Standard Templates:
              </span>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ background: "#ffffff", borderColor: "#cbd5e1", color: "#0f172a", fontWeight: 600, padding: "6px 12px" }}
                onClick={applyCourseStructurePreset}
                title="Load Standard Course Structure Format (Units 1-5, Objectives, Textbooks, COs)"
              >
                📘 Course Structure
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ background: "#ffffff", borderColor: "#cbd5e1", color: "#0f172a", fontWeight: 600, padding: "6px 12px" }}
                onClick={applyQuestionBankPreset}
                title="Load Standard Question Bank Format (Units 1-5, Part A & Part B)"
              >
                📚 Question Bank
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ background: "#eff6ff", borderColor: "#bfdbfe", color: "#1d4ed8", fontWeight: 600, padding: "6px 12px" }}
                onClick={applyMid1Preset}
                title="Load Standard I-MID Paper Format (Autonomous R-24 / 40 Marks)"
              >
                📝 Mid-1 Paper (40M)
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ background: "#eff6ff", borderColor: "#bfdbfe", color: "#1d4ed8", fontWeight: 600, padding: "6px 12px" }}
                onClick={applyMid2Preset}
                title="Load Standard II-MID Paper Format (Autonomous R-24 / 40 Marks)"
              >
                📝 Mid-2 Paper (40M)
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ background: "#faf5ff", borderColor: "#e9d5ff", color: "#7e22ce", fontWeight: 600, padding: "6px 12px" }}
                onClick={applySemesterPaperPreset}
                title="Load Standard Semester Paper Format (Autonomous R-24 / 70 Marks, Part A 20M + Part B 50M)"
              >
                📜 Semester Paper (70M)
              </button>
            </div>

            <div className="form-group">
              <label>Format Name *</label>
              <input
                type="text"
                className="form-input"
                value={formatName}
                onChange={(e) => setFormatName(e.target.value)}
                placeholder="e.g. Standard Institutional Evaluation Format"
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
      </>
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
