import React, { useState, useEffect } from "react";
import api from "../api";
import StatusBadge from "../components/StatusBadge";
import ComparisonModal from "../components/ComparisonModal";
import PdfViewerModal from "../components/PdfViewerModal";
import InstitutionLogo from "../components/InstitutionLogo";
import DepartmentDocumentsView from "../components/DepartmentDocumentsView";

function AdminDashboard({ user, activeTab = "overview" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [usersList, setUsersList] = useState([]);
  const [roleFilter, setRoleFilter] = useState("ALL");
  const [personnelSearch, setPersonnelSearch] = useState("");
  const [selectedDept, setSelectedDept] = useState(null);

  // Institution settings form
  const [instForm, setInstForm] = useState({
    name: "",
    email: "",
    logo_url: "",
  });
  const [settingsFeedback, setSettingsFeedback] = useState({ error: "", success: "" });
  const [savingSettings, setSavingSettings] = useState(false);

  // Documents search & filter
  const [docSearchQuery, setDocSearchQuery] = useState("");
  const [docStatusFilter, setDocStatusFilter] = useState("ALL");
  const [docDeptFilter, setDocDeptFilter] = useState("ALL");

  // Modals state
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [pdfModalOpen, setPdfModalOpen] = useState(false);
  const [pdfModalData, setPdfModalData] = useState({ id: null, name: "", isAccepted: false });

  useEffect(() => {
    loadDashboardData();
    loadUsers();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const res = await api.get("/admin/dashboard");
      setData(res.data);
      if (res.data?.institution) {
        setInstForm({
          name: res.data.institution.name || "",
          email: res.data.institution.email || "",
          logo_url: res.data.institution.logo_url || "",
        });
      }
    } catch (err) {
      console.error("Failed to load admin dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  // User Management Modals & Forms
  const [addUserModalOpen, setAddUserModalOpen] = useState(false);
  const [newUserForm, setNewUserForm] = useState({
    name: "",
    email: "",
    role: "Faculty",
    department_id: "",
    is_active: true,
  });
  const [userActionFeedback, setUserActionFeedback] = useState({ error: "", success: "" });

  const [editUserModalOpen, setEditUserModalOpen] = useState(false);
  const [editUserData, setEditUserData] = useState({
    id: null,
    name: "",
    email: "",
    role: "Faculty",
    department_id: "",
  });

  const loadUsers = async () => {
    try {
      const res = await api.get("/admin/users");
      setUsersList(res.data);
    } catch (err) {
      console.error("Failed to load users:", err);
    }
  };

  const handleAddUserSubmit = async (e) => {
    e.preventDefault();
    setUserActionFeedback({ error: "", success: "" });
    try {
      const res = await api.post("/admin/users", {
        name: newUserForm.name.trim(),
        email: newUserForm.email.trim(),
        role: newUserForm.role,
        department_id: newUserForm.department_id ? parseInt(newUserForm.department_id, 10) : null,
        is_active: newUserForm.is_active,
      });
      setUserActionFeedback({ error: "", success: res.data.message || `User ${newUserForm.name} added successfully!` });
      setNewUserForm({ name: "", email: "", role: "Faculty", department_id: "", is_active: true });
      setAddUserModalOpen(false);
      loadUsers();
      loadDashboardData();
    } catch (err) {
      setUserActionFeedback({ error: err.response?.data?.detail || "Failed to create user.", success: "" });
    }
  };

  const handleUpdateUserRole = async (e) => {
    e.preventDefault();
    setUserActionFeedback({ error: "", success: "" });
    try {
      const res = await api.put(`/admin/users/${editUserData.id}/role`, {
        role: editUserData.role,
        department_id: editUserData.department_id ? parseInt(editUserData.department_id, 10) : null,
      });
      setUserActionFeedback({ error: "", success: res.data.message || `Role updated successfully!` });
      setEditUserModalOpen(false);
      loadUsers();
      loadDashboardData();
    } catch (err) {
      setUserActionFeedback({ error: err.response?.data?.detail || "Failed to update role.", success: "" });
    }
  };

  const handleToggleUserStatus = async (targetUser) => {
    const nextStatus = !targetUser.is_active;
    const confirmMsg = nextStatus
      ? `Activate access for ${targetUser.name}?`
      : `Deactivate ${targetUser.name}? They will be denied system access immediately.`;
    if (!window.confirm(confirmMsg)) return;

    setUserActionFeedback({ error: "", success: "" });
    try {
      const res = await api.put(`/admin/users/${targetUser.id}/status`, { is_active: nextStatus });
      setUserActionFeedback({
        error: "",
        success: res.data.message || `User ${targetUser.name} has been ${nextStatus ? "activated" : "deactivated"}.`,
      });
      loadUsers();
      loadDashboardData();
    } catch (err) {
      setUserActionFeedback({ error: err.response?.data?.detail || "Failed to update status.", success: "" });
    }
  };

  const handleDeleteUser = async (targetUser) => {
    if (!window.confirm(`Are you sure you want to delete or deactivate account for ${targetUser.name} (${targetUser.email})?`)) return;

    setUserActionFeedback({ error: "", success: "" });
    try {
      const res = await api.delete(`/admin/users/${targetUser.id}`);
      setUserActionFeedback({ error: "", success: res.data.message || "User account updated successfully." });
      loadUsers();
      loadDashboardData();
    } catch (err) {
      setUserActionFeedback({ error: err.response?.data?.detail || "Failed to remove user account.", success: "" });
    }
  };

  const handleUpdateInstitution = async (e) => {
    e.preventDefault();
    setSettingsFeedback({ error: "", success: "" });
    setSavingSettings(true);

    try {
      const res = await api.put("/admin/institution", {
        name: instForm.name.trim(),
        email: instForm.email.trim(),
        logo_url: instForm.logo_url.trim() || null,
      });
      setSettingsFeedback({
        error: "",
        success: "Institution information and settings updated successfully!",
      });
      loadDashboardData();
    } catch (err) {
      setSettingsFeedback({
        error: err.response?.data?.detail || "Failed to update institution settings.",
        success: "",
      });
    } finally {
      setSavingSettings(false);
    }
  };

  const openComparisonModal = async (docId) => {
    try {
      const res = await api.get(`/documents/${docId}/comparison`);
      setComparisonData(res.data);
      setComparisonModalOpen(true);
    } catch (err) {
      alert(err.response?.data?.detail || "Unable to load comparison breakdown.");
    }
  };

  const handleDownload = (docId) => {
    window.open(`http://localhost:8000/documents/${docId}/download`, "_blank");
  };

  if (loading && !data) {
    return (
      <div className="main-content" style={{ textAlign: "center", padding: "60px 20px" }}>
        <p style={{ color: "#64748b", fontWeight: "600" }}>Loading Institution Administration Data...</p>
      </div>
    );
  }

  const metrics = data?.metrics || {};
  const departments = data?.departments || [];
  const recentSubmissions = data?.recent_submissions || [];

  return (
    <div className="main-content">
      {/* VIEW 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div>
          {/* Key Metric Cards */}
          <div className="stats-grid">
            <div className="stat-card total">
              <span className="stat-label">Total Submissions</span>
              <span className="stat-value">{metrics.total_documents}</span>
              <span className="stat-subtext">Across all 8 branches</span>
            </div>

            <div className="stat-card accepted">
              <span className="stat-label">Strictly Accepted</span>
              <span className="stat-value accepted">{metrics.accepted_documents}</span>
              <span className="stat-subtext">
                {metrics.compliance_rate}% compliance rate
              </span>
            </div>

            <div className="stat-card rejected">
              <span className="stat-label">Strictly Rejected</span>
              <span className="stat-value rejected">{metrics.rejected_documents}</span>
              <span className="stat-subtext">Defective formatting</span>
            </div>

            <div className="stat-card pending">
              <span className="stat-label">Pending Analysis</span>
              <span className="stat-value pending">{metrics.pending_documents}</span>
              <span className="stat-subtext">Awaiting audit</span>
            </div>
          </div>

          {/* Personnel Quick Stat Row */}
          <div className="panel" style={{ padding: "20px" }}>
            <h4 style={{ fontSize: "14px", fontWeight: "700", color: "#475569", marginBottom: "14px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              👥 Institutional Personnel Overview
            </h4>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
              <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>Faculty Members</span>
                <p style={{ fontSize: "24px", fontWeight: "800", color: "#0f172a", margin: "4px 0 0" }}>{metrics.total_faculty}</p>
              </div>
              <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>Department Heads (HODs)</span>
                <p style={{ fontSize: "24px", fontWeight: "800", color: "#0f172a", margin: "4px 0 0" }}>{metrics.total_hod}</p>
              </div>
              <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>Compliance Auditors</span>
                <p style={{ fontSize: "24px", fontWeight: "800", color: "#0f172a", margin: "4px 0 0" }}>{metrics.total_auditors}</p>
              </div>
              <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                <span style={{ fontSize: "12px", color: "#64748b", fontWeight: "600" }}>Engineering Branches</span>
                <p style={{ fontSize: "24px", fontWeight: "800", color: "#0f172a", margin: "4px 0 0" }}>{metrics.total_departments}</p>
              </div>
            </div>
          </div>

          {/* Recent Institutional Submissions Audit Table */}
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Recent Institutional Document Activity</h3>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Latest PDF uploads across all departments
                </span>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={loadDashboardData}>
                ↻ Refresh
              </button>
            </div>

            {recentSubmissions.length === 0 ? (
              <p className="empty-state">No submissions recorded yet.</p>
            ) : (
              <div className="table-wrapper">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Type</th>
                      <th>Branch</th>
                      <th>Uploaded By</th>
                      <th>Date</th>
                      <th>Decision</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentSubmissions.map((doc) => (
                      <tr key={doc.id}>
                        <td><strong>{doc.file_name}</strong></td>
                        <td>{doc.document_type_name || "-"}</td>
                        <td>
                          <span className="branch-pill">
                            {doc.department_code || doc.department_name || "Institution"}
                          </span>
                        </td>
                        <td>{doc.uploaded_by_name || "Faculty"}</td>
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
                                🔍 Breakdown
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
        </div>
      )}

      {/* VIEW 2: INSTITUTION PROFILE & SETTINGS */}
      {activeTab === "institution" && (
        <div className="panel" style={{ maxWidth: "780px" }}>
          <div className="panel-header">
            <div>
              <h3>Institution Information & Branding</h3>
              <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                Manage institutional name, contact email, and custom logo emblem.
              </p>
            </div>
          </div>

          {settingsFeedback.error && (
            <div className="alert-message alert-danger">⚠️ {settingsFeedback.error}</div>
          )}
          {settingsFeedback.success && (
            <div className="alert-message alert-success">✓ {settingsFeedback.success}</div>
          )}

          <div style={{ display: "flex", gap: "24px", alignItems: "center", marginBottom: "28px", padding: "18px", background: "#f8fafc", borderRadius: "10px", border: "1px solid #e2e8f0" }}>
            <InstitutionLogo logoUrl={instForm.logo_url} size={64} />
            <div>
              <h4 style={{ margin: "0 0 4px", fontSize: "16px", fontWeight: "700" }}>
                {instForm.name || "Institution"}
              </h4>
              <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
                Active College Profile • Logo displays across Sidebar, Login, and Documents
              </p>
            </div>
          </div>

          <form onSubmit={handleUpdateInstitution}>
            <div className="form-group">
              <label>Institution Legal Name *</label>
              <input
                type="text"
                className="form-input"
                value={instForm.name}
                onChange={(e) => setInstForm({ ...instForm, name: e.target.value })}
                placeholder="e.g. Anantha Lakshmi Institute of Technology and Sciences"
                required
              />
            </div>

            <div className="form-group">
              <label>Official Institutional Contact Email *</label>
              <input
                type="email"
                className="form-input"
                value={instForm.email}
                onChange={(e) => setInstForm({ ...instForm, email: e.target.value })}
                placeholder="administration@institution.edu"
                required
              />
            </div>

            <div className="form-group">
              <label>Institution Logo URL (Optional)</label>
              <input
                type="url"
                className="form-input"
                value={instForm.logo_url}
                onChange={(e) => setInstForm({ ...instForm, logo_url: e.target.value })}
                placeholder="https://example.com/logo.png or leave empty to use standard collegiate crest"
              />
              <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                Leave blank to automatically use the institutional collegiate seal crest.
              </p>
            </div>

            <button type="submit" className="btn btn-primary" disabled={savingSettings}>
              {savingSettings ? "Saving Settings..." : "💾 Save Changes"}
            </button>
          </form>
        </div>
      )}

      {/* VIEW 3: PERSONNEL DIRECTORY */}
      {activeTab === "personnel" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>Institutional Personnel Directory</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Registered faculty, HODs, auditors, and administrators: {usersList.length}
              </span>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => {
                  setUserActionFeedback({ error: "", success: "" });
                  setAddUserModalOpen(true);
                }}
              >
                + Add Personnel
              </button>
              <button className="btn btn-secondary btn-sm" onClick={loadUsers}>
                ↻ Refresh
              </button>
            </div>
          </div>

          {/* User action feedback */}
          {userActionFeedback.error && (
            <div className="alert-message alert-danger" style={{ margin: "12px 0" }}>
              ⚠️ {userActionFeedback.error}
            </div>
          )}
          {userActionFeedback.success && (
            <div className="alert-message alert-success" style={{ margin: "12px 0" }}>
              ✓ {userActionFeedback.success}
            </div>
          )}

          {/* Search & Filter Toolbar */}
          <div className="dashboard-toolbar">
            <div className="toolbar-controls">
              <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search staff by name or email..."
                  value={personnelSearch}
                  onChange={(e) => setPersonnelSearch(e.target.value)}
                />
              </div>

              <select
                className="toolbar-filter-select"
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
              >
                <option value="ALL">All Roles</option>
                <option value="Faculty">Faculty Only</option>
                <option value="HOD">HODs Only</option>
                <option value="Auditor">Auditors Only</option>
                <option value="Admin">Admins Only</option>
              </select>

              {(personnelSearch || roleFilter !== "ALL") && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setPersonnelSearch("");
                    setRoleFilter("ALL");
                  }}
                >
                  ✕ Reset
                </button>
              )}
            </div>

            <span className="toolbar-count">
              Showing{" "}
              {
                usersList.filter((u) => {
                  const matchesSearch =
                    !personnelSearch ||
                    (u.name && u.name.toLowerCase().includes(personnelSearch.toLowerCase())) ||
                    u.email.toLowerCase().includes(personnelSearch.toLowerCase());
                  const matchesRole = roleFilter === "ALL" || u.role === roleFilter;
                  return matchesSearch && matchesRole;
                }).length
              }{" "}
              of {usersList.length}
            </span>
          </div>

          <div className="table-wrapper">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Official Email</th>
                  <th>System Role</th>
                  <th>Assigned Department</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {usersList
                  .filter((u) => {
                    const matchesSearch =
                      !personnelSearch ||
                      (u.name && u.name.toLowerCase().includes(personnelSearch.toLowerCase())) ||
                      u.email.toLowerCase().includes(personnelSearch.toLowerCase());
                    const matchesRole = roleFilter === "ALL" || u.role === roleFilter;
                    return matchesSearch && matchesRole;
                  })
                  .map((u) => (
                    <tr key={u.id}>
                      <td><strong>{u.name || "Colleague"}</strong></td>
                      <td><code>{u.email}</code></td>
                      <td>
                        <span className={`role-tag role-${u.role}`}>{u.role}</span>
                      </td>
                      <td>{u.department_name ? `${u.department_code} - ${u.department_name}` : "Institution-Wide"}</td>
                      <td>
                        {u.is_active ? (
                          <span style={{ background: "#dcfce7", color: "#15803d", padding: "3px 8px", borderRadius: "12px", fontSize: "12px", fontWeight: "600" }}>
                            Active
                          </span>
                        ) : (
                          <span style={{ background: "#fee2e2", color: "#b91c1c", padding: "3px 8px", borderRadius: "12px", fontSize: "12px", fontWeight: "600" }}>
                            Deactivated
                          </span>
                        )}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: "6px" }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            title="Edit Role / Department"
                            onClick={() => {
                              setUserActionFeedback({ error: "", success: "" });
                              setEditUserData({
                                id: u.id,
                                name: u.name,
                                email: u.email,
                                role: u.role,
                                department_id: u.department_id || "",
                              });
                              setEditUserModalOpen(true);
                            }}
                          >
                            ✎ Role
                          </button>
                          <button
                            className={`btn btn-sm ${u.is_active ? "btn-secondary" : "btn-success"}`}
                            title={u.is_active ? "Deactivate Account" : "Activate Account"}
                            onClick={() => handleToggleUserStatus(u)}
                          >
                            {u.is_active ? "Deactivate" : "Activate"}
                          </button>
                          {u.id !== user?.id && (
                            <button
                              className="btn btn-danger btn-sm"
                              title="Delete or Archive Account"
                              onClick={() => handleDeleteUser(u)}
                            >
                              🗑️
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* VIEW 4: DEPARTMENTS & BRANCHES */}
      {activeTab === "departments" && (
        selectedDept ? (
          <DepartmentDocumentsView
            department={selectedDept}
            onBack={() => setSelectedDept(null)}
            user={user}
          />
        ) : (
          <div className="panel">
            <div className="panel-header">
              <div>
                <h3>Institutional Engineering Branches ({departments.length})</h3>
                <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Click on any branch to inspect all uploaded compliance documents, evaluations, and syllabi.
                </span>
              </div>
            </div>

            <div className="table-wrapper">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Branch Code</th>
                    <th>Department / Branch Name</th>
                    <th>Faculty Count</th>
                    <th>Uploaded Documents</th>
                    <th>Accepted Records</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {departments.map((d) => (
                    <tr
                      key={d.id}
                      style={{ cursor: "pointer" }}
                      onClick={() => setSelectedDept(d)}
                      title={`Click to open ${d.name} uploaded documents`}
                    >
                      <td>
                        <span className="branch-pill" style={{ fontSize: "12px", fontWeight: "800" }}>
                          {d.code}
                        </span>
                      </td>
                      <td><strong>{d.name}</strong></td>
                      <td>{d.faculty_count} registered faculty</td>
                      <td>{d.document_count} total uploads</td>
                      <td>
                        <span style={{ color: "var(--success)", fontWeight: "700" }}>
                          {d.accepted_count} accepted
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedDept(d);
                          }}
                        >
                          📁 View Documents →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}

      {/* VIEW 5: AUDIT DOCUMENTS */}
      {activeTab === "documents" && (
        <div className="panel">
          <div className="panel-header">
            <div>
              <h3>All Institutional Submissions & Audit Status</h3>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Complete archive across all branches ({recentSubmissions.length})
              </span>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={loadDashboardData}>
              ↻ Refresh
            </button>
          </div>

          {/* Filter Toolbar */}
          <div className="dashboard-toolbar">
            <div className="toolbar-controls">
              <div className="search-input-wrapper">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  className="search-input"
                  placeholder="Search file, type, or faculty..."
                  value={docSearchQuery}
                  onChange={(e) => setDocSearchQuery(e.target.value)}
                />
              </div>

              <select
                className="toolbar-filter-select"
                value={docStatusFilter}
                onChange={(e) => setDocStatusFilter(e.target.value)}
              >
                <option value="ALL">All Decisions</option>
                <option value="ACCEPTED">✓ Accepted</option>
                <option value="REJECTED">✕ Rejected</option>
                <option value="PENDING">⏳ Pending</option>
              </select>

              <select
                className="toolbar-filter-select"
                value={docDeptFilter}
                onChange={(e) => setDocDeptFilter(e.target.value)}
              >
                <option value="ALL">All Branches</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.code}>
                    {d.code} - {d.name}
                  </option>
                ))}
              </select>

              {(docSearchQuery || docStatusFilter !== "ALL" || docDeptFilter !== "ALL") && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setDocSearchQuery("");
                    setDocStatusFilter("ALL");
                    setDocDeptFilter("ALL");
                  }}
                >
                  ✕ Reset
                </button>
              )}
            </div>
          </div>

          <div className="table-wrapper">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Type</th>
                  <th>Branch</th>
                  <th>Uploaded By</th>
                  <th>Uploaded Date</th>
                  <th>Decision</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentSubmissions
                  .filter((d) => {
                    const q = docSearchQuery.toLowerCase();
                    const matchesSearch =
                      !q ||
                      d.file_name.toLowerCase().includes(q) ||
                      (d.document_type_name && d.document_type_name.toLowerCase().includes(q)) ||
                      (d.uploaded_by_name && d.uploaded_by_name.toLowerCase().includes(q));
                    const matchesStatus =
                      docStatusFilter === "ALL" ||
                      d.analysis_status === docStatusFilter ||
                      (docStatusFilter === "PENDING" && (!d.analysis_status || d.analysis_status === "PENDING"));
                    const matchesDept =
                      docDeptFilter === "ALL" ||
                      d.department_code === docDeptFilter;
                    return matchesSearch && matchesStatus && matchesDept;
                  })
                  .map((doc) => (
                    <tr key={doc.id}>
                      <td><strong>{doc.file_name}</strong></td>
                      <td>{doc.document_type_name}</td>
                      <td>
                        <span className="branch-pill">
                          {doc.department_code || doc.department_name}
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
                              🔍 Breakdown
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
      {/* Add User Modal */}
      {addUserModalOpen && (
        <div className="modal-overlay" onClick={() => setAddUserModalOpen(false)}>
          <div className="modal-container" style={{ maxWidth: "520px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add New Personnel</h3>
              <button className="modal-close" onClick={() => setAddUserModalOpen(false)}>✕</button>
            </div>
            <form onSubmit={handleAddUserSubmit} style={{ padding: "20px" }}>
              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  className="form-input"
                  required
                  placeholder="e.g. Dr. Ramesh Kumar"
                  value={newUserForm.name}
                  onChange={(e) => setNewUserForm({ ...newUserForm, name: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label className="form-label">Official Email Address</label>
                <input
                  type="email"
                  className="form-input"
                  required
                  placeholder="name@institution.edu"
                  value={newUserForm.email}
                  onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label className="form-label">Institutional Role</label>
                <select
                  className="form-input"
                  value={newUserForm.role}
                  onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value })}
                >
                  <option value="Faculty">Faculty</option>
                  <option value="HOD">HOD (Head of Department)</option>
                  <option value="Auditor">Auditor</option>
                  <option value="Admin">Administrator</option>
                </select>
              </div>

              {(newUserForm.role === "Faculty" || newUserForm.role === "HOD") && (
                <div className="form-group" style={{ marginBottom: "16px" }}>
                  <label className="form-label">Assigned Department</label>
                  <select
                    className="form-input"
                    required
                    value={newUserForm.department_id}
                    onChange={(e) => setNewUserForm({ ...newUserForm, department_id: e.target.value })}
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.code} - {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "24px" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setAddUserModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Role Modal */}
      {editUserModalOpen && (
        <div className="modal-overlay" onClick={() => setEditUserModalOpen(false)}>
          <div className="modal-container" style={{ maxWidth: "500px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Edit Personnel Role & Department</h3>
              <button className="modal-close" onClick={() => setEditUserModalOpen(false)}>✕</button>
            </div>
            <form onSubmit={handleUpdateUserRole} style={{ padding: "20px" }}>
              <p style={{ margin: "0 0 16px", fontSize: "14px", color: "var(--text-muted)" }}>
                Editing permissions for <strong>{editUserData.name}</strong> (<code>{editUserData.email}</code>)
              </p>

              <div className="form-group" style={{ marginBottom: "16px" }}>
                <label className="form-label">System Role</label>
                <select
                  className="form-input"
                  value={editUserData.role}
                  onChange={(e) => setEditUserData({ ...editUserData, role: e.target.value })}
                >
                  <option value="Faculty">Faculty</option>
                  <option value="HOD">HOD (Head of Department)</option>
                  <option value="Auditor">Auditor</option>
                  <option value="Admin">Administrator</option>
                </select>
              </div>

              {(editUserData.role === "Faculty" || editUserData.role === "HOD") && (
                <div className="form-group" style={{ marginBottom: "16px" }}>
                  <label className="form-label">Assigned Department</label>
                  <select
                    className="form-input"
                    required
                    value={editUserData.department_id}
                    onChange={(e) => setEditUserData({ ...editUserData, department_id: e.target.value })}
                  >
                    <option value="">-- Select Department --</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.code} - {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "24px" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setEditUserModalOpen(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
