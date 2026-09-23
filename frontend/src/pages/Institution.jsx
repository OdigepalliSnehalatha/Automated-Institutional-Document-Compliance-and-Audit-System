import { useEffect, useState } from "react";
import api from "../api";

function Institution({ onBack }) {
  const [institutionList, setInstitutionList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchInstitutions = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await api.get("/institution");

        console.log("INSTITUTION RESPONSE:", response.data);

        const list = response.data?.institution;

        if (!Array.isArray(list)) {
          throw new Error(
            "Invalid institution data received from server"
          );
        }

        setInstitutionList(list);
      } catch (err) {
        console.error("FETCH INSTITUTIONS ERROR:", err);

        if (err.response) {
          setError(
            err.response.data?.detail ||
              "Failed to fetch institutions"
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

    fetchInstitutions();
  }, []);

  return (
    <div className="dashboard">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>Institutions</h1>

      {loading && (
        <p>Loading institutions...</p>
      )}

      {!loading && error && (
        <p style={{ color: "red" }}>
          Error fetching institutions: {error}
        </p>
      )}

      {!loading &&
        !error &&
        institutionList.length === 0 && (
          <p>No institution records found.</p>
        )}

      {!loading &&
        !error &&
        institutionList.length > 0 && (
          <div className="dashboard-cards">

            {institutionList.map((institution) => (
              <div
                className="dashboard-card"
                key={institution.id}
              >
                <h2>{institution.name}</h2>

                <p>
                  <strong>ID:</strong>{" "}
                  {institution.id}
                </p>

                <p>
                  <strong>Email:</strong>{" "}
                  {institution.email}
                </p>

                <p>
                  <strong>Created:</strong>{" "}
                  {institution.created_at || "Not available"}
                </p>
              </div>
            ))}

          </div>
        )}
    </div>
  );
}

export default Institution;