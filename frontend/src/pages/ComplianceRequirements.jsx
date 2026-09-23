import { useEffect, useState } from "react";
import api from "../api";

function ComplianceRequirements({ onBack }) {
  const [requirementList, setRequirementList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchRequirements = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get("/compliance-requirements");

        console.log(
          "COMPLIANCE REQUIREMENTS RESPONSE:",
          response.data
        );

        const list =
          response.data?.compliance_requirements;

        if (!Array.isArray(list)) {
          throw new Error(
            "Invalid compliance requirements data received from server"
          );
        }

        setRequirementList(list);
      } catch (err) {
        console.error(
          "FETCH COMPLIANCE REQUIREMENTS ERROR:",
          err
        );

        if (err.response) {
          setError(
            err.response.data?.detail ||
              "Failed to fetch compliance requirements"
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

    fetchRequirements();
  }, []);

  return (
    <div className="dashboard">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>Compliance Requirements</h1>

      {loading && (
        <p>Loading compliance requirements...</p>
      )}

      {!loading && error && (
        <p style={{ color: "red" }}>
          Error fetching compliance requirements: {error}
        </p>
      )}

      {!loading &&
        !error &&
        requirementList.length === 0 && (
          <p>No compliance requirements found.</p>
        )}

      {!loading &&
        !error &&
        requirementList.length > 0 && (
          <div className="dashboard-cards">

            {requirementList.map((requirement) => (
              <div
                className="dashboard-card"
                key={requirement.id}
              >
                <h2>{requirement.name}</h2>

                <p>
                  <strong>ID:</strong>{" "}
                  {requirement.id}
                </p>

                <p>
                  <strong>Category:</strong>{" "}
                  {requirement.category || "Not available"}
                </p>

                <p>
                  <strong>Description:</strong>{" "}
                  {requirement.description ||
                    "Not available"}
                </p>
              </div>
            ))}

          </div>
        )}
    </div>
  );
}

export default ComplianceRequirements;
