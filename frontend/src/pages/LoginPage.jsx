import React, { useState } from "react";
import api from "../api";

function LoginPage({ onLoginSuccess }) {
  const [step, setStep] = useState("credentials"); // "credentials" | "otp"
  const [formData, setFormData] = useState({
    institution_name: "Anantha Lakshmi Institute of Technology and Sciences",
    role: "Auditor",
    email: "auditor@alitsprototype.test",
    password: "",
  });
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError("");
  };

  const handleRoleSelect = (selectedRole) => {
    let defaultEmail = "";
    if (selectedRole === "Auditor") defaultEmail = "auditor@alitsprototype.test";
    else if (selectedRole === "HOD") defaultEmail = "hod.cse@alitsprototype.test";
    else if (selectedRole === "Faculty") defaultEmail = "faculty.cse@alitsprototype.test";

    setFormData({
      ...formData,
      role: selectedRole,
      email: defaultEmail,
    });
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
        password: formData.password,
      });

      if (response.data.requires_otp) {
        setStep("otp");
        setInfo(`6-digit OTP dispatched to ${formData.email}.`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please verify credentials and institution.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    if (otp.length !== 6) {
      setError("Please enter the complete 6-digit OTP.");
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
        otp: otp.trim(),
      });

      if (response.data.authenticated) {
        onLoginSuccess(response.data.user);
      }
    } catch (err) {
      setError(err.response?.data?.detail || "OTP verification failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError("");
    setInfo("");
    setLoading(true);
    try {
      await api.post("/login", {
        institution_name: formData.institution_name.trim(),
        role: formData.role,
        email: formData.email.trim(),
        password: formData.password,
      });
      setInfo("A new OTP has been dispatched to your email.");
    } catch (err) {
      setError("Unable to resend OTP. Please re-enter credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="inst-logo">🏛️</div>
          <h1>Institutional Compliance & Audit</h1>
          <p>Structural PDF Verification & Document Management</p>
        </div>

        {error && <div className="alert-message alert-danger">⚠️ {error}</div>}
        {info && <div className="alert-message alert-success">ℹ️ {info}</div>}

        {step === "credentials" ? (
          <form onSubmit={handleLoginSubmit}>
            <div className="form-group">
              <label>Institution Name</label>
              <input
                type="text"
                name="institution_name"
                className="form-input"
                value={formData.institution_name}
                onChange={handleChange}
                placeholder="e.g. Anantha Lakshmi Institute of Technology and Sciences"
                required
              />
            </div>

            <div className="form-group">
              <label>Role</label>
              <select
                name="role"
                className="form-select"
                value={formData.role}
                onChange={(e) => {
                  handleChange(e);
                  handleRoleSelect(e.target.value);
                }}
                required
              >
                <option value="Auditor">Auditor (Defines Structure, Reviews All)</option>
                <option value="HOD">HOD (Department Oversight, Accepted PDFs)</option>
                <option value="Faculty">Faculty (Uploads & Verifies PDFs)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Official Email</label>
              <input
                type="email"
                name="email"
                className="form-input"
                value={formData.email}
                onChange={handleChange}
                placeholder="registered.email@institution.edu"
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                name="password"
                className="form-input"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
                required
              />
            </div>

            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? "Authenticating..." : "Continue with OTP →"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp}>
            <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "16px" }}>
              Enter the 6-digit OTP sent to <strong>{formData.email}</strong> for role <strong>{formData.role}</strong>.
            </p>

            <div className="form-group">
              <label>6-Digit Verification OTP</label>
              <input
                type="text"
                className="form-input"
                style={{ fontSize: "20px", letterSpacing: "4px", textAlign: "center" }}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                placeholder="000000"
                maxLength={6}
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                autoFocus
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={loading || otp.length !== 6}
              style={{ marginBottom: "10px" }}
            >
              {loading ? "Verifying..." : "Verify & Access Dashboard"}
            </button>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                type="button"
                className="btn btn-secondary btn-block"
                onClick={handleResendOtp}
                disabled={loading}
              >
                Resend OTP
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-block"
                onClick={() => {
                  setStep("credentials");
                  setOtp("");
                  setError("");
                  setInfo("");
                }}
                disabled={loading}
              >
                Back
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default LoginPage;
