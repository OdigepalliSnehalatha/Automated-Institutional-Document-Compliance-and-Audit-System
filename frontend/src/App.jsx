import React, { useEffect, useState } from "react";
import api from "./api";

function App() {
  const [user, setUser] = useState(null);

  const [loginData, setLoginData] = useState({
    institution_name: "",
    role: "Faculty",
    email: "",
    password: "",
  });

  const [otp, setOtp] = useState("");
  const [otpRequired, setOtpRequired] = useState(false);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  // ---------------------------------------------------------
  // CHECK SESSION
  // ---------------------------------------------------------

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = async () => {
  try {
    const response = await api.get("/auth/me");

    if (response.data.authenticated) {
      setUser(response.data.user);
    } else {
      setUser(null);
    }
  } catch (error) {
    // 401 is normal when the user has not logged in yet.
    if (error.response?.status === 401) {
      setUser(null);
      return;
    }

    console.error("Session check failed:", error);
  }
};
  // ---------------------------------------------------------
  // LOGIN INPUT
  // ---------------------------------------------------------

  const handleLoginChange = (event) => {
    setLoginData({
      ...loginData,
      [event.target.name]: event.target.value,
    });
  };

  // ---------------------------------------------------------
  // LOGIN
  // ---------------------------------------------------------

  const handleLogin = async (event) => {
    event.preventDefault();

    setLoading(true);
    setMessage("");

    try {
      const response = await api.post("/login", loginData);

      if (response.data.requires_otp) {
        setOtpRequired(true);
        setOtp("");
        setMessage(
          "OTP has been sent to your registered email."
        );
      } else {
        setMessage(
          response.data.message ||
            "OTP has been sent to your registered email."
        );
      }
    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
          "Login failed. Please check your details."
      );
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------
  // VERIFY OTP
  // ---------------------------------------------------------

  const handleVerifyOtp = async (event) => {
    event.preventDefault();

    if (otp.length !== 6) {
      setMessage("Please enter the 6-digit OTP.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await api.post("/verify-otp", {
        institution_name: loginData.institution_name,
        role: loginData.role,
        email: loginData.email,
        otp: otp,
      });

      // Load authenticated session
      await checkSession();

      setOtpRequired(false);
      setOtp("");
      setMessage("");

    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
          "Invalid or expired OTP."
      );
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------
  // RESEND OTP
  // ---------------------------------------------------------

  const handleResendOtp = async () => {
    setLoading(true);
    setMessage("");

    try {
      const response = await api.post(
        "/login",
        loginData
      );

      if (response.data.requires_otp) {
        setOtp("");
        setMessage(
          "A new OTP has been sent to your registered email."
        );
      }

    } catch (error) {
      setMessage(
        error.response?.data?.detail ||
          "Unable to resend OTP."
      );
    } finally {
      setLoading(false);
    }
  };

  // ---------------------------------------------------------
  // BACK TO LOGIN
  // ---------------------------------------------------------

  const handleBackToLogin = () => {
    setOtpRequired(false);
    setOtp("");
    setMessage("");
  };

  // ---------------------------------------------------------
  // LOGOUT
  // ---------------------------------------------------------

  const handleLogout = async () => {
    try {
      await api.post("/logout");
    } catch (error) {
      // Session may already be expired.
    }

    setUser(null);
    setOtpRequired(false);
    setOtp("");
    setMessage("");
  };

  // =========================================================
  // LOGIN / OTP SCREEN
  // =========================================================

  if (!user) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>

          <h1>Institutional Document System</h1>

          {!otpRequired ? (

            // ------------------------------------------------
            // LOGIN FORM
            // ------------------------------------------------

            <form onSubmit={handleLogin}>

              <h2>Login</h2>

              <label>Institution Name</label>

              <input
                type="text"
                name="institution_name"
                value={loginData.institution_name}
                onChange={handleLoginChange}
                placeholder="Enter institution name"
                required
              />

              <label>Role</label>

              <select
                name="role"
                value={loginData.role}
                onChange={handleLoginChange}
                required
              >
                <option value="Auditor">
                  Auditor
                </option>

                <option value="HOD">
                  HOD
                </option>

                <option value="Faculty">
                  Faculty
                </option>
              </select>

              <label>Email</label>

              <input
                type="email"
                name="email"
                value={loginData.email}
                onChange={handleLoginChange}
                placeholder="Enter registered email"
                required
              />

              <label>Password</label>

              <input
                type="password"
                name="password"
                value={loginData.password}
                onChange={handleLoginChange}
                placeholder="Enter password"
                required
              />

              <button
                type="submit"
                disabled={loading}
              >
                {loading
                  ? "Checking..."
                  : "Login"}
              </button>

            </form>

          ) : (

            // ------------------------------------------------
            // OTP FORM
            // ------------------------------------------------

            <form onSubmit={handleVerifyOtp}>

              <h2>Verify OTP</h2>

              <p>
                Enter the 6-digit OTP sent to your
                registered email.
              </p>

              <label>OTP</label>

              <input
                type="text"
                value={otp}
                onChange={(event) => {
                  const value =
                    event.target.value.replace(
                      /\D/g,
                      ""
                    );

                  setOtp(value);
                }}
                placeholder="Enter 6-digit OTP"
                maxLength={6}
                inputMode="numeric"
                autoComplete="one-time-code"
                required
              />

              <button
                type="submit"
                disabled={
                  loading ||
                  otp.length !== 6
                }
              >
                {loading
                  ? "Verifying..."
                  : "Verify OTP"}
              </button>

              <button
                type="button"
                onClick={handleResendOtp}
                disabled={loading}
                style={styles.secondaryButton}
              >
                Resend OTP
              </button>

              <button
                type="button"
                onClick={handleBackToLogin}
                disabled={loading}
                style={styles.secondaryButton}
              >
                Back to Login
              </button>

            </form>
          )}

          {message && (
            <p style={styles.message}>
              {message}
            </p>
          )}

        </div>
      </div>
    );
  }

  // =========================================================
  // DASHBOARD
  // =========================================================

  return (
    <div style={styles.dashboard}>

      <header style={styles.header}>

        <div>

          <h1>
            Institutional Document System
          </h1>

          <p>
            <strong>Institution:</strong>{" "}
            {user.institution_name}
          </p>

          <p>
            <strong>Role:</strong>{" "}
            {user.role}
          </p>

          {user.department_name && (
            <p>
              <strong>Department:</strong>{" "}
              {user.department_name}
            </p>
          )}

        </div>

        <button onClick={handleLogout}>
          Logout
        </button>

      </header>

      <main style={styles.content}>

        {user.role === "Auditor" && (
          <div>

            <h2>Auditor Dashboard</h2>

            <p>
              Define master structural formats for:
            </p>

            <ul>
              <li>Course Structure</li>
              <li>Question Bank</li>
              <li>Question Paper</li>
            </ul>

            <p>
              You can also view structural comparisons
              and accepted PDFs.
            </p>

          </div>
        )}

        {user.role === "HOD" && (
          <div>

            <h2>HOD Dashboard</h2>

            <p>
              View accepted PDFs and structural
              comparison results for your department.
            </p>

          </div>
        )}

        {user.role === "Faculty" && (
          <div>

            <h2>Faculty Dashboard</h2>

            <p>
              Upload Course Structure, Question Bank,
              or Question Paper PDFs and run structural
              comparison.
            </p>

          </div>
        )}

      </main>

    </div>
  );
}

// =========================================================
// STYLES
// =========================================================

const styles = {

  page: {
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#f5f5f5",
  },

  card: {
    width: "420px",
    padding: "30px",
    background: "white",
    borderRadius: "10px",
    boxShadow:
      "0 4px 15px rgba(0,0,0,0.1)",
  },

  dashboard: {
    minHeight: "100vh",
    background: "#f5f5f5",
  },

  header: {
    padding: "20px 30px",
    background: "white",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    boxShadow:
      "0 2px 8px rgba(0,0,0,0.08)",
  },

  content: {
    padding: "30px",
  },

  message: {
    marginTop: "15px",
    color: "red",
  },

  secondaryButton: {
    marginTop: "10px",
    background: "#777",
  },
};

export default App;