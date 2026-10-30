import React, { useState, useEffect } from "react";
import api from "./api";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import LogoutModal from "./components/LogoutModal";
import AiAssistantModal from "./components/AiAssistantModal";
import LoginPage from "./pages/LoginPage";
import AdminDashboard from "./pages/AdminDashboard";
import AuditorDashboard from "./pages/AuditorDashboard";
import HodDashboard from "./pages/HodDashboard";
import FacultyDashboard from "./pages/FacultyDashboard";
import QuestionPaperManagement from "./pages/QuestionPaperManagement";

function App() {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [logoutModalOpen, setLogoutModalOpen] = useState(false);
  const [logoutFeedback, setLogoutFeedback] = useState("");
  const [notifications, setNotifications] = useState([
    {
      title: "Boolean Decision Engine Ready",
      time: "Active",
      message: "100% structural verification active for all branches.",
    },
    {
      title: "New Branch Added",
      time: "Recent",
      message: "CAI (Computer Artificial Intelligence) is live for compliance.",
    },
  ]);

  useEffect(() => {
    restoreSession();
  }, []);

  const restoreSession = async () => {
    try {
      const response = await api.get("/auth/me");
      if (response.data?.authenticated && response.data?.user) {
        setUser(response.data.user);
        setDefaultTabForRole(response.data.user.role);
      } else {
        setUser(null);
      }
    } catch (error) {
      setUser(null);
    } finally {
      setInitializing(false);
    }
  };

  const setDefaultTabForRole = (role) => {
    if (role === "Faculty") setActiveTab("evaluations");
    else setActiveTab("overview");
  };

  const handleConfirmLogout = async () => {
    try {
      await api.post("/logout");
    } catch (e) {
      // Session may already be expired
    }
    setLogoutModalOpen(false);
    setUser(null);
    setActiveTab("overview");
    setLogoutFeedback("You have securely signed out of your institutional session.");
  };

  // Get dynamic title for topbar
  const getHeaderTitles = () => {
    if (!user) return { title: "Dashboard", subtitle: "" };

    if (activeTab === "question_papers" || activeTab === "evaluations") {
      return {
        title: "Evaluations",
        subtitle: "Multi-examination institutional document evaluations and approvals",
        subtitle: "Multi-examination paper tracking, automated structural verification, and institutional approvals"
      };
    }

    const titlesMap = {
      Admin: {
        overview: { title: "Institutional Executive Overview", subtitle: "High-level metrics, compliance rates, and department statistics" },
        institution: { title: "Institution Profile & Branding", subtitle: "Configure legal name, contact email, and custom logo emblem" },
        personnel: { title: "Institutional Personnel Directory", subtitle: "Manage registered faculty members, department heads, and auditors" },
        departments: { title: "Engineering Branches & Departments", subtitle: "Overview of active college departments including CAI, CSE, ECE" },
        documents: { title: "Institutional Compliance Documents", subtitle: "Audit records across all engineering departments" },
      },
      Auditor: {
        overview: { title: "Structural Audit & Analytics", subtitle: "Overview of institutional document verification" },
        builder: { title: "Structural Format Builder", subtitle: "Configure rule requirements without writing code" },
        formats: { title: "Master Structural Formats", subtitle: "Defined compliance blueprints and active templates" },
        submissions: { title: "Institutional Submitted Documents", subtitle: "Audit documents submitted by faculty members across all branches" },
        accepted: { title: "Accepted Official Records", subtitle: "Strictly verified PDFs meeting 100% structural compliance" },
      },
      HOD: {
        overview: { title: "Department Compliance Dashboard", subtitle: `Submissions and audit status for ${user.department_name || "Department"}` },
        all: { title: "Faculty Document Submissions", subtitle: "Review faculty PDF uploads and structural analysis breakdowns" },
        accepted: { title: "Verified Compliant Documents", subtitle: "Official accepted PDFs available for authorized HOD download" },
        branches: { title: "Institutional Department Guidelines", subtitle: "Multi-branch guidelines including CAI, CSE, and ECE" },
      },
      Faculty: {
        upload: { title: "Document Upload & Verification", subtitle: "Upload institutional PDFs for automated PyMuPDF structural analysis" },
        submissions: { title: "My Submitted Documents", subtitle: "Track compliance decisions, re-analyze files, and view diagnostics" },
        guidelines: { title: "Compliance Rules & Guidelines", subtitle: "Mandatory structural formatting checklist for high-probability acceptance" },
      },
    };

    const roleMap = titlesMap[user.role] || titlesMap.Faculty;
    return roleMap[activeTab] || { title: "Dashboard", subtitle: `Logged in as ${user.role}` };
  };

  if (initializing) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc" }}>
        <div style={{ textAlign: "center", color: "#64748b" }}>
          <div style={{ fontSize: "38px", marginBottom: "12px" }}>🏛️</div>
          <p style={{ fontWeight: "700", color: "#0f172a" }}>Loading Institutional Compliance System...</p>
          <span style={{ fontSize: "12px", color: "#94a3b8" }}>Restoring secure session cookie...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <LoginPage
        onLoginSuccess={(authenticatedUser) => {
          setLogoutFeedback("");
          setUser(authenticatedUser);
          setDefaultTabForRole(authenticatedUser.role);
        }}
        initialInfo={logoutFeedback}
      />
    );
  }

  const headerInfo = getHeaderTitles();

  return (
    <div className="app-shell">
      {/* 1. FIXED LEFT SIDEBAR */}
      <Sidebar
        user={user}
        activeTab={activeTab}
        onSelectTab={(tabId) => setActiveTab(tabId)}
        onRequestLogout={() => setLogoutModalOpen(true)}
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* 2. RIGHT MAIN VIEWPORT */}
      <div className="app-main-viewport">
        {/* Sticky Desktop Topbar Header */}
        <Topbar
          user={user}
          title={headerInfo.title}
          subtitle={headerInfo.subtitle}
          onOpenMobileMenu={() => setMobileMenuOpen(true)}
          notifications={notifications}
        />

        {/* Active Dashboard View based on User Role */}
        <main className="dashboard-content-area" style={{ flex: 1, padding: "20px 24px" }}>
          {activeTab === "question_papers" || activeTab === "evaluations" ? (
            <QuestionPaperManagement user={user} />
          ) : user.role === "Admin" ? (
            <AdminDashboard user={user} activeTab={activeTab} />
          ) : user.role === "Auditor" ? (
            <AuditorDashboard
              user={user}
              activeTab={activeTab}
              onTabChange={(newTab) => setActiveTab(newTab)}
            />
          ) : user.role === "HOD" ? (
            <HodDashboard
              user={user}
              activeTab={activeTab}
              onTabChange={(newTab) => setActiveTab(newTab)}
            />
          ) : (
            <FacultyDashboard
              user={user}
              activeTab={activeTab}
              onTabChange={(newTab) => setActiveTab(newTab)}
            />
          )}
        </main>
      </div>

      {/* 3. ROLE-AWARE AI CHATBOT MODAL & FLOATING BUTTON */}
      <AiAssistantModal
        user={user}
        isOpen={aiModalOpen}
        onClose={() => setAiModalOpen(false)}
        onOpen={() => setAiModalOpen(true)}
      />

      {/* 4. LOGOUT CONFIRMATION DIALOG */}
      <LogoutModal
        isOpen={logoutModalOpen}
        onClose={() => setLogoutModalOpen(false)}
        onConfirm={handleConfirmLogout}
        user={user}
      />
    </div>
  );
}

export default App;
