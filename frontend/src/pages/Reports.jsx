import { useEffect, useState } from "react";
import api from "../api";

function Reports({ onBack }) {
  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingReport, setLoadingReport] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await api.get("/audit-reports");

        setReports(
          response.data.audit_reports || []
        );
      } catch (err) {
        console.error(
          "Error fetching reports:",
          err
        );

        setError(
          err.response?.data?.detail ||
          "Unable to load audit reports"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  const viewReport = async (reportId) => {
    setLoadingReport(true);
    setError("");

    try {
      const reportResponse = await api.get(
        `/audit-reports/${reportId}`
      );

      setSelectedReport(
        reportResponse.data
      );

      const findingsResponse =
        await api.get("/audit-findings");

      const allFindings =
        findingsResponse.data.audit_findings || [];

      const reportFindings =
        allFindings.filter(
          (finding) =>
            finding.audit_id ===
            reportResponse.data.audit_id
        );

      setFindings(reportFindings);

    } catch (err) {
      console.error(
        "Error fetching report:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Unable to load report"
      );
    } finally {
      setLoadingReport(false);
    }
  };

  const parseReportContent = (content) => {
    if (!content) {
      return {
        score: null,
        results: []
      };
    }

    const scoreMatch =
      content.match(
        /Compliance Score:\s*([\d.]+)%/
      );

    const score = scoreMatch
      ? parseFloat(scoreMatch[1])
      : null;

    const resultSection =
      content.split(
        "COMPLIANCE RESULTS"
      )[1] || "";

    const blocks =
      resultSection.split(
        "-----------------------------------"
      );

    const results = [];

    blocks.forEach((block) => {
      const checkId =
        block.match(
          /Check ID:\s*(\d+)/
        );

      const requirementId =
        block.match(
          /Requirement ID:\s*(\d+)/
        );

      const complianceCode =
        block.match(
          /Compliance Code:\s*(.+)/
        );

      const requirement =
        block.match(
          /Requirement:\s*(.+)/
        );

      const status =
        block.match(
          /Status:\s*(.+)/
        );

      const evidence =
        block.match(
          /Evidence:\s*(.+)/
        );

      if (checkId) {
        results.push({
          checkId: checkId[1],
          requirementId:
            requirementId
              ? requirementId[1]
              : "",
          complianceCode:
            complianceCode
              ? complianceCode[1].trim()
              : "",
          requirement:
            requirement
              ? requirement[1].trim()
              : "",
          status:
            status
              ? status[1].trim()
              : "",
          evidence:
            evidence
              ? evidence[1].trim()
              : ""
        });
      }
    });

    return {
      score,
      results
    };
  };

  const reportData =
    selectedReport
      ? parseReportContent(
          selectedReport.report_content
        )
      : null;

  return (
    <div className="page">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>Audit Reports</h1>

      {loading && (
        <p>Loading reports...</p>
      )}

      {error && (
        <p>{error}</p>
      )}

      {!loading &&
        !error &&
        reports.length === 0 && (
          <p>
            No audit reports found.
          </p>
        )}

      {!loading &&
        !error &&
        reports.length > 0 && (
          <div>

            {reports.map((report) => (
              <div
                key={report.id}
                className="dashboard-card"
              >

                <h2>
                  {report.report_name}
                </h2>

                <p>
                  Report ID: {report.id}
                </p>

                <p>
                  Audit ID: {report.audit_id}
                </p>

                <p>
                  Document ID: {report.document_id}
                </p>

                <p>
                  Department ID: {report.department_id}
                </p>

                <button
                  onClick={() =>
                    viewReport(report.id)
                  }
                >
                  View Report Details
                </button>

              </div>
            ))}

          </div>
        )}

      {loadingReport && (
        <p>
          Loading report details...
        </p>
      )}

      {selectedReport &&
        reportData && (
          <div>

            {/* Report Information */}

            <div className="dashboard-card">

              <h2>
                Compliance Report
              </h2>

              <p>
                <strong>
                  Report Name:
                </strong>{" "}
                {selectedReport.report_name}
              </p>

              <p>
                <strong>
                  Report ID:
                </strong>{" "}
                {selectedReport.id}
              </p>

              <p>
                <strong>
                  Audit ID:
                </strong>{" "}
                {selectedReport.audit_id}
              </p>

              <p>
                <strong>
                  Document ID:
                </strong>{" "}
                {selectedReport.document_id}
              </p>

              <p>
                <strong>
                  Department ID:
                </strong>{" "}
                {selectedReport.department_id}
              </p>

            </div>

            {/* Compliance Score */}

            <div className="dashboard-card">

              <h2>
                Compliance Score
              </h2>

              <h1>
                {reportData.score !== null
                  ? `${reportData.score}%`
                  : "N/A"}
              </h1>

            </div>

            {/* Compliance Results */}

            <h2>
              Compliance Results
            </h2>

            {reportData.results.map(
              (result) => (
                <div
                  key={result.checkId}
                  className="dashboard-card"
                >

                  <h3>
                    {result.status ===
                    "Compliant"
                      ? "✓ Compliant"
                      : "✗ Non-Compliant"}
                  </h3>

                  <p>
                    <strong>
                      Compliance Code:
                    </strong>{" "}
                    {result.complianceCode}
                  </p>

                  <p>
                    <strong>
                      Requirement:
                    </strong>{" "}
                    {result.requirement}
                  </p>

                  <p>
                    <strong>
                      Check ID:
                    </strong>{" "}
                    {result.checkId}
                  </p>

                  <p>
                    <strong>
                      Requirement ID:
                    </strong>{" "}
                    {result.requirementId}
                  </p>

                  <p>
                    <strong>
                      Status:
                    </strong>{" "}
                    {result.status}
                  </p>

                  <p>
                    <strong>
                      Evidence:
                    </strong>{" "}
                    {result.evidence}
                  </p>

                </div>
              )
            )}

            {/* Audit Findings */}

            <h2>
              Audit Findings
            </h2>

            {findings.length === 0 ? (
              <div className="dashboard-card">
                <p>
                  No findings for this audit.
                </p>
              </div>
            ) : (
              findings.map((finding) => (
                <div
                  key={finding.id}
                  className="dashboard-card"
                >

                  <h3>
                    Finding
                  </h3>

                  <p>
                    <strong>
                      Requirement ID:
                    </strong>{" "}
                    {finding.requirement_id}
                  </p>

                  <p>
                    <strong>
                      Severity:
                    </strong>{" "}
                    {finding.severity}
                  </p>

                  <p>
                    <strong>
                      Finding:
                    </strong>{" "}
                    {finding.finding}
                  </p>

                  <p>
                    <strong>
                      Recommendation:
                    </strong>{" "}
                    {finding.recommendation}
                  </p>

                </div>
              ))
            )}

          </div>
        )}

    </div>
  );
}

export default Reports;