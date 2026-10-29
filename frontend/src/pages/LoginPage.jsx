import React, { useState, useEffect, useRef } from "react";
import api from "../api";
import InstitutionLogo from "../components/InstitutionLogo";
import AuthIllustration from "../components/AuthIllustration";

function LoginPage({ onLoginSuccess, initialInfo }) {
  // Navigation mode: "login" | "register" | "forgot"
  const [authMode, setAuthMode] = useState("login");
  const [step, setStep] = useState("form"); // "form" | "otp" (for forgot password)

  // Form Data
  const [loginData, setLoginData] = useState({
    institution_name: "Anantha Lakshmi Institute of Technology and Sciences",
    email: "",
    password: "",
  });

  const [registerData, setRegisterData] = useState({
    institution_name: "Anantha Lakshmi Institute of Technology and Sciences",
    name: "",
    email: "",
    role: "Faculty",
    department_id: "",
    password: "",
    confirmPassword: "",
  });

  const [forgotData, setForgotData] = useState({
    email: "",
    newPassword: "",
    confirmNewPassword: "",
  });

  // Departments list for registration dropdown
  const [departments, setDepartments] = useState([]);
  const [departmentsLoading, setDepartmentsLoading] = useState(false);

  // 6-digit OTP for Forgot Password
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const otpInputRefs = useRef([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState(initialInfo || "");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Fetch departments on mount
  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    try {
      setDepartmentsLoading(true);
      const res = await api.get("/departments");
      if (Array.isArray(res.data) && res.data.length > 0) {
        setDepartments(res.data);
        setRegisterData((prev) => ({
          ...prev,
          department_id: prev.department_id || String(res.data[0].id),
        }));
      }
    } catch (e) {
      console.error("Failed to load departments list", e);
    } finally {
      setDepartmentsLoading(false);
    }
  };

  const switchToLogin = () => {
    setAuthMode("login");
    setStep("form");
    setError("");
    setInfo("");
  };

  const switchToRegister = () => {
    setAuthMode("register");
    setStep("form");
    setError("");
    setInfo("");
  };

  const switchToForgot = () => {
    setAuthMode("forgot");
    setStep("email");
    setError("");
    setInfo("");
    setOtpDigits(["", "", "", "", "", ""]);
  };

  const handleLoginChange = (e) => {
    const { name, value } = e.target;
    setLoginData((prev) => ({ ...prev, [name]: value }));
    setError("");
  };

  const handleRegisterChange = (e) => {
    const { name, value } = e.target;
    setRegisterData((prev) => ({ ...prev, [name]: value }));
    setError("");
  };

  const handleForgotChange = (e) => {
    const { name, value } = e.target;
    setForgotData((prev) => ({ ...prev, [name]: value }));
    setError("");
  };

  // Quick autofill demo credentials for testing
  const applyQuickLogin = (email, password) => {
    setLoginData((prev) => ({ ...prev, email, password }));
    setError("");
    setInfo(`Loaded demo credentials for ${email}`);
  };

  // 1. DIRECT EMAIL & PASSWORD LOGIN (No OTP needed for normal login)
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!loginData.email.trim()) {
      setError("Please enter your registered email address.");
      return;
    }
    if (!loginData.password) {
      setError("Please enter your password.");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post("/login", {
        institution_name: loginData.institution_name.trim(),
        email: loginData.email.trim(),
        password: loginData.password,
      });

      if (response.data.authenticated && response.data.user) {
        onLoginSuccess(response.data.user);
      } else {
        setError("Authentication was inconclusive. Please try again.");
      }
    } catch (err) {
      const errMsg = err.response?.data?.detail || "Invalid email or password. Please try again.";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  // 2. REGISTRATION (Collects name, email, password, role, department)
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!registerData.name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!registerData.email.trim()) {
      setError("Please enter your official institutional email.");
      return;
    }
    if (registerData.password.length < 6) {
      setError("Password must be at least 6 characters in length.");
      return;
    }
    if (registerData.password !== registerData.confirmPassword) {
      setError("Passwords do not match. Please re-enter.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        institution_name: registerData.institution_name.trim(),
        name: registerData.name.trim(),
        email: registerData.email.trim(),
        role: registerData.role,
        department_id: ["Faculty", "HOD"].includes(registerData.role) && registerData.department_id ? parseInt(registerData.department_id) : null,
        password: registerData.password,
      };

      const res = await api.post("/register", payload);

      if (res.data.success && res.data.user) {
        // Automatically log user into their authorized dashboard
        onLoginSuccess(res.data.user);
      } else {
        setInfo(res.data.message || "Account created! You can now log in.");
        switchToLogin();
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed. An account with this email may already exist.");
    } finally {
      setLoading(false);
    }
  };

  // 3. FORGOT PASSWORD (OTP flow)
  const handleOtpChange = (index, value) => {
    const cleaned = value.replace(/\D/g, "");
    if (!cleaned) {
      const updated = [...otpDigits];
      updated[index] = "";
      setOtpDigits(updated);
      return;
    }
    const digit = cleaned.slice(-1);
    const updated = [...otpDigits];
    updated[index] = digit;
    setOtpDigits(updated);
    setError("");

    if (index < 5 && digit) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowLeft" && index > 0) {
      otpInputRefs.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const fullOtp = otpDigits.join("");

  const handleRequestPasswordReset = async (e) => {
    e.preventDefault();
    if (!forgotData.email.trim()) {
      setError("Please enter your registered email address.");
      return;
    }
    setError("");
    setInfo("");
    setLoading(true);

    try {
      const res = await api.post("/forgot-password", {
        email: forgotData.email.trim(),
      });
      setStep("otp-reset");
      if (res.data.otp) {
        setOtpDigits(res.data.otp.split(""));
        setInfo(`📬 Reset code: ${res.data.otp}`);
      } else {
        setInfo(res.data.message || `Password reset code sent to ${forgotData.email.trim()}.`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Password reset request failed. Please check your email.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPasswordSubmit = async (e) => {
    e.preventDefault();
    if (fullOtp.length !== 6) {
      setError("Please enter the complete 6-digit passcode.");
      return;
    }
    if (forgotData.newPassword.length < 6) {
      setError("New password must be at least 6 characters.");
      return;
    }
    if (forgotData.newPassword !== forgotData.confirmNewPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError("");
    setInfo("");
    setLoading(true);

    try {
      await api.post("/reset-password", {
        email: forgotData.email.trim(),
        otp: fullOtp,
        new_password: forgotData.newPassword,
      });

      switchToLogin();
      setInfo("✅ Password reset successfully! You can now log in with your new password.");
      setLoginData((prev) => ({ ...prev, email: forgotData.email.trim(), password: "" }));
    } catch (err) {
      setError(err.response?.data?.detail || "Password reset failed. Please verify your OTP code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-split-page">
      {/* LEFT SIDE: Hero & Branding */}
      <div className="login-split-hero">
        <div className="hero-content-wrapper">
          <div className="hero-header-brand">
            <InstitutionLogo size={54} />
            <div>
              <h1 className="hero-institution-title">
                {loginData.institution_name}
              </h1>
              <p className="hero-system-subtitle">
                Automated Institutional Compliance & Document Audit System
              </p>
            </div>
          </div>

          <div className="hero-illustration-container">
            <AuthIllustration />
          </div>

          <div className="hero-features-list">
            <div className="hero-feature-item">
              <span className="feature-icon">🛡️</span>
              <div>
                <strong>Boolean Decision Compliance</strong>
                <p>100% strict layout rule validation for Question Papers & Syllabi</p>
              </div>
            </div>

            <div className="hero-feature-item">
              <span className="feature-icon">⚡</span>
              <div>
                <strong>Automated PDF Structural Analysis</strong>
                <p>Instant detection of Part A / Part B sections, marks schemes & question counts</p>
              </div>
            </div>

            <div className="hero-feature-item">
              <span className="feature-icon">🏢</span>
              <div>
                <strong>Institutional Multi-Role Governance</strong>
                <p>Role-enforced permissions for Admin, Auditor, HOD, and Faculty</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT SIDE: Authentication Card */}
      <div className="login-split-form-pane">
        <div className="login-form-card" style={{ maxWidth: "480px" }}>
          
          {/* Top Tabs: Sign In vs Create Account */}
          {authMode !== "forgot" && (
            <div className="auth-nav-tabs">
              <button
                type="button"
                className={`auth-nav-tab ${authMode === "login" ? "active" : ""}`}
                onClick={switchToLogin}
                disabled={loading}
              >
                🔒 Sign In
              </button>
              <button
                type="button"
                className={`auth-nav-tab ${authMode === "register" ? "active" : ""}`}
                onClick={switchToRegister}
                disabled={loading}
              >
                📝 Create Account
              </button>
            </div>
          )}

          {/* Form Header */}
          <div className="form-card-header">
            <div className="form-card-badge">SECURE INSTITUTIONAL PORTAL</div>
            <h2 className="form-card-title">
              {authMode === "login" && "Sign in to your Account"}
              {authMode === "register" && "Institutional User Registration"}
              {authMode === "forgot" && step === "email" && "Reset Forgotten Password"}
              {authMode === "forgot" && step === "otp-reset" && "Set New Password"}
            </h2>
            <p className="form-card-desc">
              {authMode === "login" && "Enter your registered email and password to open your authorized institutional dashboard."}
              {authMode === "register" && "Fill in your institutional credentials and assigned role to create an account."}
              {authMode === "forgot" && step === "email" && "Enter your registered email to receive a password reset verification code."}
              {authMode === "forgot" && step === "otp-reset" && `Enter the verification code sent to ${forgotData.email}`}
            </p>
          </div>

          {/* Alerts */}
          {error && <div className="alert-message alert-danger">⚠️ {error}</div>}
          {info && <div className="alert-message alert-success">ℹ️ {info}</div>}

          {/* =========================================================
              VIEW 1: DIRECT LOGIN FORM (Email + Password)
          ========================================================== */}
          {authMode === "login" && (
            <form onSubmit={handleLoginSubmit} className="login-form-body">
              <div className="form-group">
                <label className="form-label">Institution Scope</label>
                <input
                  type="text"
                  name="institution_name"
                  className="form-input"
                  value={loginData.institution_name}
                  onChange={handleLoginChange}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Official Registered Email</label>
                <input
                  type="email"
                  name="email"
                  className="form-input"
                  value={loginData.email}
                  onChange={handleLoginChange}
                  placeholder="name@institution.edu"
                  autoComplete="email"
                  required
                />
              </div>

              <div className="form-group">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <label className="form-label" style={{ margin: 0 }}>Password</label>
                  <button
                    type="button"
                    className="auth-link-btn"
                    onClick={switchToForgot}
                    style={{ fontSize: "12px", background: "none", border: "none", color: "var(--primary)", cursor: "pointer", padding: 0 }}
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="password-input-wrapper" style={{ position: "relative" }}>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="form-input"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    placeholder="Enter account password"
                    autoComplete="current-password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                    aria-label="Toggle password visibility"
                  >
                    {showPassword ? "👁️" : "👁️‍🗨️"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block"
                style={{ padding: "12px", fontSize: "15px", fontWeight: 600, marginTop: "8px" }}
                disabled={loading}
              >
                {loading ? "Authenticating..." : "Sign In to Dashboard →"}
              </button>

              {/* Quick Demo Access (Equal 4-Role Grid) */}
              <div style={{ marginTop: "20px", paddingTop: "14px", borderTop: "1px dashed var(--border-color)" }}>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.6px", fontWeight: 700, display: "block", marginBottom: "8px" }}>
                  ⚡ Quick Demo Accounts (Click to Fill):
                </span>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    style={{ fontSize: "12px", padding: "8px 10px", textAlign: "left", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                    onClick={() => applyQuickLogin("admin@alits.ac.in", "Admin@123")}
                  >
                    🛡️ Admin
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    style={{ fontSize: "12px", padding: "8px 10px", textAlign: "left", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                    onClick={() => applyQuickLogin("hod.cse@alits.ac.in", "HOD@123")}
                  >
                    🏛️ HOD
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    style={{ fontSize: "12px", padding: "8px 10px", textAlign: "left", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                    onClick={() => applyQuickLogin("auditor@alits.ac.in", "Auditor@123")}
                  >
                    📊 Auditor
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    style={{ fontSize: "12px", padding: "8px 10px", textAlign: "left", borderRadius: "8px", border: "1px solid #e2e8f0" }}
                    onClick={() => applyQuickLogin("faculty.cse@alits.ac.in", "Faculty@123")}
                  >
                    🎓 Faculty
                  </button>
                </div>
              </div>
</form>
          )}

          {/* =========================================================
              VIEW 2: REGISTRATION FORM (Role & Dept collected)
          ========================================================== */}
          {authMode === "register" && (
            <form onSubmit={handleRegisterSubmit} className="login-form-body">
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  type="text"
                  name="name"
                  className="form-input"
                  value={registerData.name}
                  onChange={handleRegisterChange}
                  placeholder="e.g. Dr. Rajesh Sharma"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Official Email Address</label>
                <input
                  type="email"
                  name="email"
                  className="form-input"
                  value={registerData.email}
                  onChange={handleRegisterChange}
                  placeholder="name@alits.ac.in"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Assigned Institutional Role</label>
                <select
                  name="role"
                  className="form-input"
                  value={registerData.role}
                  onChange={handleRegisterChange}
                  required
                >
                  <option value="Faculty">Faculty Member</option>
                  <option value="HOD">Head of Department (HOD)</option>
                  <option value="Auditor">Institutional Compliance Auditor</option>
                  <option value="Admin">Administrator / Institution Head</option>
                </select>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px", display: "block" }}>
                  Role permissions are enforced strictly on the server backend.
                </span>
              </div>

              {["Faculty", "HOD"].includes(registerData.role) && (
                <div className="form-group">
                  <label className="form-label">Engineering Department</label>
                  <select
                    name="department_id"
                    className="form-input"
                    value={registerData.department_id}
                    onChange={handleRegisterChange}
                    required
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.code} - {d.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Password</label>
                <div className="password-input-wrapper" style={{ position: "relative" }}>
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="form-input"
                    value={registerData.password}
                    onChange={handleRegisterChange}
                    placeholder="Create a strong password (min 6 chars)"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex="-1"
                  >
                    {showPassword ? "👁️" : "👁️‍🗨️"}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm Password</label>
                <div className="password-input-wrapper" style={{ position: "relative" }}>
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    className="form-input"
                    value={registerData.confirmPassword}
                    onChange={handleRegisterChange}
                    placeholder="Re-enter password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex="-1"
                  >
                    {showConfirmPassword ? "👁️" : "👁️‍🗨️"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block"
                style={{ padding: "12px", fontSize: "15px", fontWeight: 600, marginTop: "8px" }}
                disabled={loading}
              >
                {loading ? "Creating Account..." : "Create Account & Sign In →"}
              </button>

              <div style={{ textAlign: "center", marginTop: "16px" }}>
                <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={switchToLogin}
                    style={{ background: "none", border: "none", color: "var(--primary)", fontWeight: 600, cursor: "pointer" }}
                  >
                    Sign In
                  </button>
                </span>
              </div>
            </form>
          )}

          {/* =========================================================
              VIEW 3: FORGOT PASSWORD (OTP Reset)
          ========================================================== */}
          {authMode === "forgot" && step === "email" && (
            <form onSubmit={handleRequestPasswordReset} className="login-form-body">
              <div className="form-group">
                <label className="form-label">Registered Email</label>
                <input
                  type="email"
                  name="email"
                  className="form-input"
                  value={forgotData.email}
                  onChange={handleForgotChange}
                  placeholder="name@institution.edu"
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block"
                style={{ padding: "12px", fontSize: "15px", fontWeight: 600, marginTop: "8px" }}
                disabled={loading}
              >
                {loading ? "Dispatching Code..." : "Send Verification Passcode"}
              </button>

              <div style={{ textAlign: "center", marginTop: "16px" }}>
                <button
                  type="button"
                  onClick={switchToLogin}
                  style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "13px", cursor: "pointer" }}
                >
                  ← Return to Sign In
                </button>
              </div>
            </form>
          )}

          {authMode === "forgot" && step === "otp-reset" && (
            <form onSubmit={handleResetPasswordSubmit} className="login-form-body">
              <div className="form-group">
                <label className="form-label">6-Digit Passcode</label>
                <div className="otp-digit-boxes" style={{ display: "flex", gap: "8px", justifyContent: "center" }}>
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (otpInputRefs.current[idx] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      className="otp-digit-input"
                      value={digit}
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                      style={{ width: "42px", height: "48px", textAlign: "center", fontSize: "18px", fontWeight: 700 }}
                    />
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">New Password</label>
                <input
                  type="password"
                  name="newPassword"
                  className="form-input"
                  value={forgotData.newPassword}
                  onChange={handleForgotChange}
                  placeholder="Min 6 characters"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Confirm New Password</label>
                <input
                  type="password"
                  name="confirmNewPassword"
                  className="form-input"
                  value={forgotData.confirmNewPassword}
                  onChange={handleForgotChange}
                  placeholder="Re-enter new password"
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block"
                style={{ padding: "12px", fontSize: "15px", fontWeight: 600, marginTop: "8px" }}
                disabled={loading || fullOtp.length !== 6}
              >
                {loading ? "Updating..." : "Update Password & Return to Sign In"}
              </button>

              <div style={{ textAlign: "center", marginTop: "16px" }}>
                <button
                  type="button"
                  onClick={switchToLogin}
                  style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "13px", cursor: "pointer" }}
                >
                  ← Cancel and return to Sign In
                </button>
              </div>
            </form>
          )}

        </div>
      </div>
    </div>
  );
}

export default LoginPage;
