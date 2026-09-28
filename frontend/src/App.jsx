import React, { useState, useEffect } from "react";
import api from "./api";
import Navbar from "./components/Navbar";
import LoginPage from "./pages/LoginPage";
import AuditorDashboard from "./pages/AuditorDashboard";
import HodDashboard from "./pages/HodDashboard";
import FacultyDashboard from "./pages/FacultyDashboard";

function App() {
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    restoreSession();
  }, []);

  const restoreSession = async () => {
    try {
      const response = await api.get("/auth/me");
      if (response.data?.authenticated && response.data?.user) {
        setUser(response.data.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      // 401 is expected when the user is not logged in yet.
      setUser(null);
    } finally {
      setInitializing(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.post("/logout");
    } catch (e) {
      // Session may already be expired
    }
    setUser(null);
  };

  if (initializing) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc" }}>
        <div style={{ textAlign: "center", color: "#64748b" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🏛️</div>
          <p style={{ fontWeight: "600" }}>Loading Institutional Compliance System...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLoginSuccess={(authenticatedUser) => setUser(authenticatedUser)} />;
  }

  return (
    <div className="app-layout">
      <Navbar user={user} onLogout={handleLogout} />

      {user.role === "Auditor" && <AuditorDashboard user={user} />}
      {user.role === "HOD" && <HodDashboard user={user} />}
      {user.role === "Faculty" && <FacultyDashboard user={user} />}
    </div>
  );
}

export default App;