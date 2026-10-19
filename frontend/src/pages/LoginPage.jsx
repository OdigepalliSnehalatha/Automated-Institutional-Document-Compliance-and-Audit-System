import React, { useState, useEffect, useRef } from "react";
import api from "../api";
import InstitutionLogo from "../components/InstitutionLogo";
import AuthIllustration from "../components/AuthIllustration";

function LoginPage({ onLoginSuccess, initialInfo }) {
  const [step, setStep] = useState("credentials"); // "credentials" | "otp"
  const [formData, setFormData] = useState({
    institution_name: "Anantha Lakshmi Institute of Technology and Sciences",
    role: "Faculty",
    email: "",
    password: "",
  });

  // 6 individual OTP box digits
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const otpInputRefs = useRef([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState(initialInfo || "");
  const [showPassword, setShowPassword] = useState(false);

  // Countdown timer for OTP expiry (5 minutes = 300 seconds)
  // Cooldown timer for OTP resend (60 seconds)
  const [timerSeconds, setTimerSeconds] = useState(300);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);

  useEffect(() => {
    let timer;
    if (step === "otp" && timerSeconds > 0) {
      timer = setInterval(() => {
        setTimerSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
        setCooldownSeconds((prev) => (prev <= 1 ? 0 : prev - 1));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step, timerSeconds]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError("");
  };

  const handleRoleSelect = (selectedRole) => {
    setFormData((prev) => ({
      ...prev,
      role: selectedRole,
    }));
    setError("");
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setInfo("");
    setLoading(true);

    try {
      const response = await api.post("/login", {
        institution_name: formData.institution_name.trim(),
        role: formData.role,
        email: formData.email.trim(),
        password: formData.password || undefined,
      });

      if (response.data.requires_otp) {
        setStep("otp");
        setTimerSeconds(300); // 5 minutes
        setCooldownSeconds(0);
        const receivedOtp = response.data.otp;
        if (receivedOtp && receivedOtp.length === 6) {
          setOtpDigits(receivedOtp.split(""));
          setInfo(`📬 Verification code generated for ${formData.email.trim()}: ${receivedOtp}`);
        } else {
          setOtpDigits(["", "", "", "", "", ""]);
          setInfo(response.data.message || `A verification passcode has been dispatched to ${formData.email.trim()}.`);
        }
        setTimeout(() => {
          otpInputRefs.current[5]?.focus();
        }, 150);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Authentication failed. Please verify your credentials and institution.");
    } finally {
      setLoading(false);
    }
  };

  // Handle individual OTP inputs
  const handleOtpChange = (index, value) => {
    // Only accept numeric digit
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

    // Auto-advance to next box
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

  const handleVerifyOtp = async (e) => {
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
        institution_name: formData.institution_name.trim(),
        role: formData.role,
        email: formData.email.trim(),
        otp: fullOtp,
      });

      if (response.data.authenticated) {
        onLoginSuccess(response.data.user);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid or expired OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (loading) return;
    setError("");
    setInfo("");
    setLoading(true);

    try {
      const res = await api.post("/login", {
        institution_name: formData.institution_name.trim(),
        role: formData.role,
        email: formData.email.trim(),
      });
      setTimerSeconds(300);
      setCooldownSeconds(0);
      const receivedOtp = res.data.otp;
      if (receivedOtp && receivedOtp.length === 6) {
        setOtpDigits(receivedOtp.split(""));
        setInfo(`📬 Fresh verification code generated for ${formData.email}: ${receivedOtp}`);
      } else {
        setOtpDigits(["", "", "", "", "", ""]);
        setInfo(res.data.message || `A fresh 6-digit verification code has been dispatched to ${formData.email}.`);
      }
      setTimeout(() => {
        otpInputRefs.current[5]?.focus();
      }, 100);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to resend code. Please return to login and re-enter your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="login-split-page">
      {/* LEFT SIDE: Hero & Institutional Branding */}
      <div className="login-split-hero">
        <div className="hero-content-wrapper">
          <div className="hero-header-brand">
            <InstitutionLogo size={52} />
            <div>
              <h1 className="hero-institution-title">
                {formData.institution_name}
              </h1>
              <p className="hero-system-subtitle">
                Automated Institutional Compliance & Document Audit System
              </p>
            </div>
          </div>

          {/* Educational Art Illustration */}
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
          {/* Header */}
          <div className="form-card-header">
            <div className="form-card-badge">SECURE INSTITUTIONAL PORTAL</div>
            <h2 className="form-card-title">
              {step === "credentials" ? "Sign in to your Account" : "Verify Security Code"}
            </h2>
            <p className="form-card-desc">
              {step === "credentials"
                ? "Enter your official credentials to request a one-time passcode (OTP)."
                : `Enter the 6-digit code sent to ${formData.email}`}
            </p>
          </div>

          {/* Alerts */}
          {error && <div className="alert-message alert-danger">⚠️ {error}</div>}
          {info && <div className="alert-message alert-success">ℹ️ {info}</div>}

          {/* STEP 1: CREDENTIALS FORM */}
          {step === "credentials" ? (
            <form onSubmit={handleLoginSubmit} className="login-form-body">
              <div className="form-group">
                <label className="form-label">Institution Scope</label>
                <input
                  type="text"
                  name="institution_name"
                  className="form-input"
                  value={formData.institution_name}
                  onChange={handleChange}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Select Role</label>
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
                      className={`role-select-pill ${formData.role === r.id ? "active" : ""}`}
                      onClick={() => handleRoleSelect(r.id)}
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
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="name@institution.edu"
                  required
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || !formData.email.trim()}
              >
                {loading ? "Verifying Email & Sending OTP..." : "Send Verification OTP →"}
              </button>
            </form>
          ) : (
            /* STEP 2: 6-DIGIT OTP VERIFICATION FORM */
            <form onSubmit={handleVerifyOtp} className="login-form-body">
              <div className="otp-boxes-wrapper" onPaste={handleOtpPaste}>
                <label className="form-label" style={{ display: "block", marginBottom: "12px", textAlign: "center" }}>
                  Enter 6-Digit One-Time Passcode
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
                    <span style={{ color: "var(--danger)" }}>Code expired. Please request a new OTP.</span>
                  )}
                </span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block btn-lg"
                disabled={loading || fullOtp.length !== 6 || timerSeconds === 0}
                style={{ marginTop: "16px" }}
              >
                {loading ? "Verifying Passcode..." : "Verify & Access Dashboard"}
              </button>

              <div className="otp-secondary-actions">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={handleResendOtp}
                  disabled={loading}
                >
                  ↻ Resend Passcode
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setStep("credentials");
                    setError("");
                    setInfo("");
                  }}
                  disabled={loading}
                >
                  ← Change Email / Back
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
