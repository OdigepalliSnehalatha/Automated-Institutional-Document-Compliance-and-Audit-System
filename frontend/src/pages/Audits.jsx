import { useEffect, useState } from "react";
import api from "../api";

function Audits({ onBack }) {
  const [auditList, setAuditList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAudits = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get("/audits");

        console.log("AUDITS RESPONSE:", response.data);

        const list = response.data?.audits;

        if (!Array.isArray(list)) {
          throw new Error(
            "Invalid audit data received from server"
          );
        }

        setAuditList(list);
      } catch (err) {
        console.error("FETCH AUDITS ERROR:", err);

        if (err.response) {
          setError(
            err.response.data?.detail ||
              "Failed to fetch audits"
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

    fetchAudits();
  }, []);

  return (
    <div className="dashboard">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>Audits</h1>

      {loading && (
        <p>Loading audits...</p>
      )}

      {!loading && error && (
        <p style={{ color: "red" }}>
          Error fetching audits: {error}
        </p>
      )}

      {!loading &&
        !error &&
        auditList.length === 0 && (
          <p>No audit records found.</p>
        )}

      {!loading &&
        !error &&
        auditList.length > 0 && (
          <div className="dashboard-cards">

            {auditList.map((audit) => (
              <div
                className="dashboard-card"
                key={audit.id}
              >
                <h2>Audit #{audit.id}</h2>

                <p>
                  <strong>Institution ID:</strong>{" "}
                  {audit.institution_id}
                </p>

                <p>
                  <strong>Status:</strong>{" "}
                  {audit.status}
                </p>

                <p>
                  <strong>Audit Date:</strong>{" "}
                  {audit.audit_date || "Not available"}
                </p>

                <p>
                  <strong>Created:</strong>{" "}
                  {audit.created_at || "Not available"}
                </p>
              </div>
            ))}

          </div>
        )}
    </div>
  );
}

export default Audits;