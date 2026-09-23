import { useEffect, useState } from "react";
import api from "../api";

function ComplianceChecks({ onBack }) {
  const [checkList, setCheckList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchChecks = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get("/compliance-checks");

        console.log("COMPLIANCE CHECKS RESPONSE:", response.data);

        const list = response.data?.compliance_checks;

        if (!Array.isArray(list)) {
          throw new Error(
            "Invalid compliance checks data received from server"
          );
        }

        setCheckList(list);
      } catch (err) {
        console.error("FETCH COMPLIANCE CHECKS ERROR:", err);

        if (err.response) {
          setError(
            err.response.data?.detail ||
              "Failed to fetch compliance checks"
          );
        } else {
          setError(
            err.message ||
              "Unable to connect to the server"
          );
        }
      } finally {
        setLoading(false);
      }
    };

    fetchChecks();
  }, []);

  return (
    <div className="dashboard">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>Compliance Checks</h1>

      {loading && (
        <p>Loading compliance checks...</p>
      )}

      {!loading && error && (
        <p style={{ color: "red" }}>
          Error fetching compliance checks: {error}
        </p>
      )}

      {!loading &&
        !error &&
        checkList.length === 0 && (
          <p>No compliance checks found.</p>
        )}

      {!loading &&
        !error &&
        checkList.length > 0 && (
          <div className="dashboard-cards">

            {checkList.map((check) => (
              <div
                className="dashboard-card"
                key={check.id}
              >
                <h2>Check #{check.id}</h2>

                <p>
                  <strong>Audit ID:</strong>{" "}
                  {check.audit_id}
                </p>

                <p>
                  <strong>Requirement ID:</strong>{" "}
                  {check.requirement_id}
                </p>

                <p>
                  <strong>Status:</strong>{" "}
                  {check.status}
                </p>

                <p>
                  <strong>Checked At:</strong>{" "}
                  {check.checked_at || "Not available"}
                </p>
              </div>
            ))}

          </div>
        )}
    </div>
  );
}

export default ComplianceChecks;