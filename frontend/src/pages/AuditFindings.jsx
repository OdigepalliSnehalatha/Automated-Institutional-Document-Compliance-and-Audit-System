import { useEffect, useState } from "react";
import api from "../api";

function AuditFindings({ onBack }) {
  const [findingList, setFindingList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchFindings = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get("/audit-findings");

        console.log("AUDIT FINDINGS RESPONSE:", response.data);

        const list = response.data?.audit_findings;

        if (!Array.isArray(list)) {
          throw new Error(
            "Invalid audit findings data received from server"
          );
        }

        setFindingList(list);
      } catch (err) {
        console.error("FETCH AUDIT FINDINGS ERROR:", err);

        if (err.response) {
          setError(
            err.response.data?.detail ||
              "Failed to fetch audit findings"
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

    fetchFindings();
  }, []);

  return (
    <div className="dashboard">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>Audit Findings</h1>

      {loading && (
        <p>Loading audit findings...</p>
      )}

      {!loading && error && (
        <p style={{ color: "red" }}>
          Error fetching audit findings: {error}
        </p>
      )}

      {!loading &&
        !error &&
        findingList.length === 0 && (
          <p>No audit findings found.</p>
        )}

      {!loading &&
        !error &&
        findingList.length > 0 && (
          <div className="dashboard-cards">

            {findingList.map((finding) => (
              <div
                className="dashboard-card"
                key={finding.id}
              >
                <h2>Finding #{finding.id}</h2>

                <p>
                  <strong>Audit ID:</strong>{" "}
                  {finding.audit_id}
                </p>

                <p>
                  <strong>Requirement ID:</strong>{" "}
                  {finding.requirement_id}
                </p>

                <p>
                  <strong>Severity:</strong>{" "}
                  {finding.severity}
                </p>

                <p>
                  <strong>Description:</strong>{" "}
                  {finding.description || "Not available"}
                </p>
              </div>
            ))}

          </div>
        )}
    </div>
  );
}

export default AuditFindings;