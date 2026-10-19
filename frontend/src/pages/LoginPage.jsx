import React, { useState, useEffect, useRef } from "react";
import api from "../api";
import InstitutionLogo from "../components/InstitutionLogo";
import AuthIllustration from "../components/AuthIllustration";

function LoginPage({ onLoginSuccess, initialInfo }) {
  // Navigation mode: "login" | "register" | "forgot"
  const [authMode, setAuthMode] = useState("login");
  
  // Steps within modes:
  // For login: "form" | "otp"
  // For register: "form" | "otp"
  // For forgot: "email" | "otp-reset"
  const [step, setStep] = useState("form");

  // Form Data
  const [loginData, setLoginData] = useState({
    institution_name: "Anantha Lakshmi Institute of Technology and Sciences",
    role: "Faculty",
    email: "",
    password: "",
  });

  const [registerData, setRegisterData] = useState({
    institution_name: "Anantha Lakshmi Institute of Technology and Sciences",
    name: "",
    email: "",
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

  // 6 individual OTP box digits
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const otpInputRefs = useRef([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState(initialInfo || "");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Timers: Expiration (300s = 5m), Resend Cooldown (60s)
  const [timerSeconds, setTimerSeconds] = useState(300);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);

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

  // Cooldown & Expiry Timer Interval
  useEffect(() => {
    let timer;
    if (step === "otp" && timerSeconds > 0) {
      timer = setInterval(() => {
        setTimerSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step, timerSeconds]);

  useEffect(() => {
    let timer;
    if (cooldownSeconds > 0) {
      timer = setInterval(() => {
        setCooldownSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldownSeconds]);

  // Mode Switch Handlers
  const switchToLogin = () => {
    setAuthMode("login");
    setStep("form");
    setError("");
    setInfo("");
    setOtpDigits(["", "", "", "", "", ""]);
  };

  const switchToRegister = () => {
    setAuthMode("register");
    setStep("form");
    setError("");
    setInfo("");
    setOtpDigits(["", "", "", "", "", ""]);
    if (departments.length === 0) {
      fetchDepartments();
    }
  };

  const switchToForgot = () => {
    setAuthMode("forgot");
    setStep("email");
    setError("");
    setInfo("");
    setOtpDigits(["", "", "", "", "", ""]);
  };

  // Input change handlers
  const handleLoginChange = (e) => {
    setLoginData({ ...loginData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleRegisterChange = (e) => {
    setRegisterData({ ...registerData, [e.target.name]: e.target.value });
    setError("");
  };

  const handleForgotChange = (e) => {
    setForgotData({ ...forgotData, [e.target.name]: e.target.value });
    setError("");
  };

  // ==========================================
  // OTP Box Management
  // ==========================================
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

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (!pasted) return;

    const newDigits = [...otpDigits];
    for (let i = 0; i < 6; i++) {
      newDigits[i] = pasted[i] || "";
    }
    setOtpDigits(newDigits);
    setError("");

    const nextIndex = Math.min(pasted.length, 5);
    otpInputRefs.current[nextIndex]?.focus();
  };

  const fullOtp = otpDigits.join("");

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // ==========================================
  // 1. LOGIN WORKFLOW
  // ==========================================
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!loginData.email.trim()) {
      setError("Please enter your official email address.");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post("/login", {
        institution_name: loginData.institution_name.trim(),
        role: loginData.role,
        email: loginData.email.trim(),
        password: loginData.password ? loginData.password.trim() : undefined,
      });

      if (response.data.requires_otp) {
        setStep("otp");
        setTimerSeconds(300);
        setCooldownSeconds(60);
        setOtpDigits(["", "", "", "", "", ""]);
        setInfo(response.data.message || `A verification passcode has been dispatched to ${loginData.email.trim()}.`);
        setTimeout(() => otpInputRefs.current[0]?.focus(), 150);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication failed. Please verify your credentials and institution.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyLoginOtp = async (e) => {
    e.preventDefault();
    if (fullOtp.length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setError("");
    setInfo("");
    setLoading(true);

    try {
      const response = await api.post("/verify-otp", {
        institution_name: loginData.institution_name.trim(),
        role: loginData.role,
        email: loginData.email.trim(),
        otp: fullOtp,
      });

      if (response.data.authenticated && response.data.user) {
        onLoginSuccess(response.data.user);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendLoginOtp = async () => {
    if (loading || cooldownSeconds > 0) return;
    setError("");
    setInfo("");
    setLoading(true);

    try {
      const res = await api.post("/login", {
        institution_name: loginData.institution_name.trim(),
        role: loginData.role,
        email: loginData.email.trim(),
        password: loginData.password ? loginData.password.trim() : undefined,
      });
      setTimerSeconds(300);
      setCooldownSeconds(60);
      setOtpDigits(["", "", "", "", "", ""]);
      setInfo(res.data.message || `A fresh 6-digit verification code has been dispatched to ${loginData.email.trim()}.`);
      setTimeout(() => otpInputRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to resend passcode. Please check email address.");
    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  // 2. REGISTRATION WORKFLOW
  // ==========================================
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!registerData.name.trim()) {
      setError("Please enter your full official name.");
      return;
    }
    if (!registerData.email.trim() || !registerData.email.includes("@")) {
      setError("Please enter a valid official email address.");
      return;
    }
    if (registerData.password.length < 6) {
      setError("Password must contain at least 6 characters.");
      return;
    }
    if (registerData.password !== registerData.confirmPassword) {
      setError("Password and confirmation password do not match.");
      return;
    }

    setLoading(true);
    try {
      const response = await api.post("/register", {
        name: registerData.name.trim(),
        email: registerData.email.trim(),
        password: registerData.password,
        department_id: registerData.department_id ? parseInt(registerData.department_id, 10) : undefined,
        institution_name: registerData.institution_name,
      });

      if (response.data.requires_verification) {
        setStep("otp");
        setTimerSeconds(300);
        setCooldownSeconds(60);
        setOtpDigits(["", "", "", "", "", ""]);
        setInfo(response.data.message || `A verification code has been dispatched to ${registerData.email.trim()}.`);
        setTimeout(() => otpInputRefs.current[0]?.focus(), 150);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Registration request failed. Please verify your details.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyRegisterOtp = async (e) => {
    e.preventDefault();
    if (fullOtp.length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setError("");
    setInfo("");
    setLoading(true);

    try {
      const response = await api.post("/verify-registration", {
        email: registerData.email.trim(),
        otp: fullOtp,
      });

      if (response.data.authenticated && response.data.user) {
        onLoginSuccess(response.data.user);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired registration code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendRegisterOtp = async () => {
    if (loading || cooldownSeconds > 0) return;
    setError("");
    setInfo("");
    setLoading(true);

    try {
      const res = await api.post("/register", {
        name: registerData.name.trim(),
        email: registerData.email.trim(),
        password: registerData.password,
        department_id: registerData.department_id ? parseInt(registerData.department_id, 10) : undefined,
        institution_name: registerData.institution_name,
      });
      setTimerSeconds(300);
      setCooldownSeconds(60);
      setOtpDigits(["", "", "", "", "", ""]);
      setInfo(res.data.message || `A fresh registration passcode has been dispatched to ${registerData.email.trim()}.`);
      setTimeout(() => otpInputRefs.current[0]?.focus(), 100);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to resend registration code.");
    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  // 3. FORGOT / RESET PASSWORD WORKFLOW
  // ==========================================
  const handleForgotSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");

    if (!forgotData.email.trim()) {
      setError("Please enter your registered email address.");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post("/forgot-password", {
        email: forgotData.email.trim(),
      });
      setStep("otp-reset");
      setTimerSeconds(300);
      setCooldownSeconds(60);
      setOtpDigits(["", "", "", "", "", ""]);
      setInfo(res.data.message || `Password reset code sent to ${forgotData.email.trim()}.`);
      setTimeout(() => otpInputRefs.current[0]?.focus(), 150);
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
      setError("New password and confirm password do not match.");
      return;
    }

    setError("");
    setInfo("");
    setLoading(true);

    try {
      const res = await api.post("/reset-password", {
        email: forgotData.email.trim(),
        otp: fullOtp,
        new_password: forgotData.newPassword,
      });

      // Reset successful, return to login form
      switchToLogin();
      setInfo("✅ Password reset successfully! You can now log in with your new credentials.");
      setLoginData((prev) => ({ ...prev, email: forgotData.email.trim(), password: "" }));
    } catch (err) {
      setError(err.response?.data?.detail || "Password reset failed. Please verify your OTP.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-split-page">
      {/* LEFT SIDE: Hero & Institutional Branding */}
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

          {/* Educational Campus Art Illustration */}
          <div className="hero-illustration-container">
            <AuthIllustration />
          </div>

          {/* Feature Highlights */}
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
                <strong>Automated PyMuPDF Analysis</strong>
                <p>Instant detection of structural sections, marks patterns & question counts</p>
              </div>
            </div>

            <div className="hero-feature-item">
              <span className="feature-icon">🏢</span>
              <div>
                <strong>Multi-Branch Governance</strong>
                <p>Unified support for 8 engineering branches including CAI, CSE, ECE</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT SIDE: Authentication Card */}
      <div className="login-split-form-pane">
        <div className="login-form-card">
          
          {/* TOP NAVIGATION TABS: Sign In vs Create Account */}
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

          {/* Header */}
          <div className="form-card-header">
            <div className="form-card-badge">SECURE INSTITUTIONAL PORTAL</div>
            <h2 className="form-card-title">
              {authMode === "login" && step === "form" && "Sign in to your Account"}
              {authMode === "login" && step === "otp" && "Verify Security Passcode"}
              {authMode === "register" && step === "form" && "Institutional Registration"}
              {authMode === "register" && step === "otp" && "Verify Account Passcode"}
              {authMode === "forgot" && step === "email" && "Reset Forgotten Password"}
              {authMode === "forgot" && step === "otp-reset" && "Set New Password"}
            </h2>
            <p className="form-card-desc">
              {authMode === "login" && step === "form" && "Enter your registered email and credentials to receive a one-time login code."}
              {authMode === "login" && step === "otp" && `Enter the 6-digit security code sent to ${loginData.email}`}
              {authMode === "register" && step === "form" && "Register with your official details. An email verification code will be sent to activate your account."}
              {authMode === "register" && step === "otp" && `Enter the 6-digit registration code sent to ${registerData.email}`}
              {authMode === "forgot" && step === "email" && "Enter your registered email to receive a password reset verification code."}
              {authMode === "forgot" && step === "otp-reset" && `Enter the code sent to ${forgotData.email} and choose a new password.`}
            </p>
          </div>

          {/* Alerts */}
          {error && <div className="alert-message alert-danger">⚠️ {error}</div>}
          {info && <div className="alert-message alert-success">ℹ️ {info}</div>}

          {/* =========================================================
              VIEW 1: LOGIN FORM
          ========================================================== */}
          {authMode === "login" && step === "form" && (
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
                <label className="form-label">Assigned Institutional Role</label>
                <div className="role-selector-grid">
                  {[
                    { id: "Admin", label: "Admin", icon: "🛡️" },
                    { id: "Auditor", label: "Auditor", icon: "📊" },
                    { id: "HOD", label: "HOD", icon: "🏛️" },
                    { id: "Faculty", label: "Faculty", icon: "🎓" },
                  ].map((r) => (
                    <button
                      type="button"
                      key={r.id}
                      className={`role-select-pill ${loginData.role === r.id ? "active" : ""}`}
                      onClick={() => {
                        setLoginData((prev) => ({ ...prev, role: r.id }));
                        setError("");
                      }}
                    >
                      <span className="role-pill-icon">{r.icon}</span>
                      <span className="role-pill-text">{r.label}</span>
                    </button>
                  ))}
                </div>
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
                  >
                    Forgot Password?
                  </button>
                </div>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="form-input"
                    value={loginData.password}
                    onChange={handleLoginChange}
                    placeholder="Enter account password"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? "👁️" : "🔒"}
                  </button>
                </div>
                <span className="auth-input-helper">Optional if account was created with OTP-only verification.</span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || !loginData.email.trim()}
              >
                {loading ? "Verifying & Sending Passcode..." : "Send Verification Passcode →"}
              </button>

              <div className="auth-sub-links">
                <span>New to the system?</span>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={switchToRegister}
                >
                  Create Faculty Account →
                </button>
              </div>
            </form>
          )}

          {/* =========================================================
              VIEW 2: LOGIN OTP VERIFICATION
          ========================================================== */}
          {authMode === "login" && step === "otp" && (
            <form onSubmit={handleVerifyLoginOtp} className="login-form-body">
              <div className="otp-boxes-wrapper" onPaste={handleOtpPaste}>
                <label className="form-label" style={{ display: "block", marginBottom: "12px", textAlign: "center" }}>
                  Enter 6-Digit Verification Passcode
                </label>
                <div className="otp-digit-inputs">
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (otpInputRefs.current[idx] = el)}
                      type="text"
                      className="otp-digit-box"
                      value={digit}
                      maxLength={1}
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                      disabled={loading}
                      required
                    />
                  ))}
                </div>
              </div>

              {/* Countdown Timer */}
              <div className="otp-timer-row">
                <span className="otp-timer-icon">⏱️</span>
                <span className="otp-timer-text">
                  {timerSeconds > 0 ? (
                    <>Code expires in: <strong>{formatTimer(timerSeconds)}</strong></>
                  ) : (
                    <span style={{ color: "var(--danger)" }}>Passcode expired. Please request a new one.</span>
                  )}
                </span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || fullOtp.length !== 6 || timerSeconds === 0}
                style={{ marginTop: "14px" }}
              >
                {loading ? "Verifying Passcode..." : "Verify Passcode & Access Dashboard →"}
              </button>

              <div className="otp-secondary-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleResendLoginOtp}
                  disabled={loading || cooldownSeconds > 0}
                >
                  {cooldownSeconds > 0
                    ? `↻ Resend (${cooldownSeconds}s)`
                    : "↻ Resend Passcode"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setStep("form");
                    setError("");
                    setInfo("");
                  }}
                  disabled={loading}
                >
                  ← Back to Login
                </button>
              </div>
            </form>
          )}

          {/* =========================================================
              VIEW 3: REGISTRATION FORM
          ========================================================== */}
          {authMode === "register" && step === "form" && (
            <form onSubmit={handleRegisterSubmit} className="login-form-body">
              <div className="auth-notice-banner">
                <span>ℹ️</span>
                <span>
                  Self-registration activates an authorized <strong>Faculty</strong> account. Administrative & Auditor access is granted via the Administrator Directory.
                </span>
              </div>

              <div className="form-group">
                <label className="form-label">Full Official Name</label>
                <input
                  type="text"
                  name="name"
                  className="form-input"
                  value={registerData.name}
                  onChange={handleRegisterChange}
                  placeholder="Prof. / Dr. / First Last"
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
                  placeholder="name@institution.edu"
                  autoComplete="email"
                  required
                />
                <span className="auth-input-helper">A real verification passcode will be sent to this exact inbox.</span>
              </div>

              <div className="form-group">
                <label className="form-label">Assigned Engineering Department</label>
                <select
                  name="department_id"
                  className="form-select"
                  value={registerData.department_id}
                  onChange={handleRegisterChange}
                  disabled={departmentsLoading}
                  required
                >
                  {departmentsLoading ? (
                    <option>Loading departments...</option>
                  ) : (
                    departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>
                        {dept.code} — {dept.name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Create Password</label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    className="form-input"
                    value={registerData.password}
                    onChange={handleRegisterChange}
                    placeholder="Minimum 6 characters"
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? "👁️" : "🔒"}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm Password</label>
                <div className="password-input-wrapper">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmPassword"
                    className="form-input"
                    value={registerData.confirmPassword}
                    onChange={handleRegisterChange}
                    placeholder="Re-enter password"
                    autoComplete="new-password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? "👁️" : "🔒"}
                  </button>
                </div>
                {registerData.confirmPassword && registerData.password !== registerData.confirmPassword && (
                  <span style={{ fontSize: "11px", color: "var(--danger)", marginTop: "4px", display: "block" }}>
                    ❌ Passwords do not match
                  </span>
                )}
                {registerData.confirmPassword && registerData.password === registerData.confirmPassword && (
                  <span style={{ fontSize: "11px", color: "var(--success)", marginTop: "4px", display: "block" }}>
                    ✓ Passwords match
                  </span>
                )}
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || !registerData.name.trim() || !registerData.email.trim() || !registerData.password}
              >
                {loading ? "Registering & Sending Verification Code..." : "Create Account & Send Code →"}
              </button>

              <div className="auth-sub-links">
                <span>Already registered?</span>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={switchToLogin}
                >
                  ← Sign In Here
                </button>
              </div>
            </form>
          )}

          {/* =========================================================
              VIEW 4: REGISTRATION OTP VERIFICATION
          ========================================================== */}
          {authMode === "register" && step === "otp" && (
            <form onSubmit={handleVerifyRegisterOtp} className="login-form-body">
              <div className="otp-boxes-wrapper" onPaste={handleOtpPaste}>
                <label className="form-label" style={{ display: "block", marginBottom: "12px", textAlign: "center" }}>
                  Enter 6-Digit Email Verification Code
                </label>
                <div className="otp-digit-inputs">
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (otpInputRefs.current[idx] = el)}
                      type="text"
                      className="otp-digit-box"
                      value={digit}
                      maxLength={1}
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                      disabled={loading}
                      required
                    />
                  ))}
                </div>
              </div>

              {/* Countdown Timer */}
              <div className="otp-timer-row">
                <span className="otp-timer-icon">⏱️</span>
                <span className="otp-timer-text">
                  {timerSeconds > 0 ? (
                    <>Code expires in: <strong>{formatTimer(timerSeconds)}</strong></>
                  ) : (
                    <span style={{ color: "var(--danger)" }}>Code expired. Please request a new code.</span>
                  )}
                </span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || fullOtp.length !== 6 || timerSeconds === 0}
                style={{ marginTop: "14px" }}
              >
                {loading ? "Activating Account..." : "Verify & Activate Institutional Account →"}
              </button>

              <div className="otp-secondary-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleResendRegisterOtp}
                  disabled={loading || cooldownSeconds > 0}
                >
                  {cooldownSeconds > 0
                    ? `↻ Resend (${cooldownSeconds}s)`
                    : "↻ Resend Code"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setStep("form");
                    setError("");
                    setInfo("");
                  }}
                  disabled={loading}
                >
                  ← Edit Registration
                </button>
              </div>
            </form>
          )}

          {/* =========================================================
              VIEW 5: FORGOT PASSWORD - REQUEST EMAIL
          ========================================================== */}
          {authMode === "forgot" && step === "email" && (
            <form onSubmit={handleForgotSubmit} className="login-form-body">
              <div className="form-group">
                <label className="form-label">Registered Account Email</label>
                <input
                  type="email"
                  name="email"
                  className="form-input"
                  value={forgotData.email}
                  onChange={handleForgotChange}
                  placeholder="name@institution.edu"
                  autoComplete="email"
                  required
                />
                <span className="auth-input-helper">We will send a 6-digit security code to reset your password.</span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || !forgotData.email.trim()}
              >
                {loading ? "Sending Reset Passcode..." : "Send Reset Passcode →"}
              </button>

              <div className="auth-sub-links" style={{ justifyContent: "center" }}>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={switchToLogin}
                >
                  ← Return to Sign In
                </button>
              </div>
            </form>
          )}

          {/* =========================================================
              VIEW 6: FORGOT PASSWORD - OTP & NEW PASSWORD
          ========================================================== */}
          {authMode === "forgot" && step === "otp-reset" && (
            <form onSubmit={handleResetPasswordSubmit} className="login-form-body">
              <div className="otp-boxes-wrapper" onPaste={handleOtpPaste}>
                <label className="form-label" style={{ display: "block", marginBottom: "12px", textAlign: "center" }}>
                  Enter 6-Digit Reset Passcode
                </label>
                <div className="otp-digit-inputs">
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (otpInputRefs.current[idx] = el)}
                      type="text"
                      className="otp-digit-box"
                      value={digit}
                      maxLength={1}
                      inputMode="numeric"
                      onChange={(e) => handleOtpChange(idx, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                      disabled={loading}
                      required
                    />
                  ))}
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">New Password</label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="newPassword"
                    className="form-input"
                    value={forgotData.newPassword}
                    onChange={handleForgotChange}
                    placeholder="Minimum 6 characters"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? "👁️" : "🔒"}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Confirm New Password</label>
                <div className="password-input-wrapper">
                  <input
                    type={showConfirmPassword ? "text" : "password"}
                    name="confirmNewPassword"
                    className="form-input"
                    value={forgotData.confirmNewPassword}
                    onChange={handleForgotChange}
                    placeholder="Re-enter new password"
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle-btn"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? "👁️" : "🔒"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || fullOtp.length !== 6 || !forgotData.newPassword}
              >
                {loading ? "Resetting Password..." : "Update Password & Return to Login →"}
              </button>

              <div className="auth-sub-links" style={{ justifyContent: "center" }}>
                <button
                  type="button"
                  className="auth-link-btn"
                  onClick={switchToLogin}
                >
                  ← Cancel & Return to Sign In
                </button>
              </div>
            </form>
          )}

          {/* Footer note */}
          <div className="form-card-footer">
            <span>🔒 Protected by Role-Based Encryption & Session Token Security</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
