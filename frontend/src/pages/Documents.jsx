import { useEffect, useState } from "react";
import api from "../api";

function Documents({ onBack }) {
  const [documentList, setDocumentList] = useState([]);

  const [institutionId, setInstitutionId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [documentTypeId, setDocumentTypeId] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);

  const [documentTypes, setDocumentTypes] = useState([]);

  const [loading, setLoading] = useState(true);
  const [loadingTypes, setLoadingTypes] = useState(true);
  const [uploading, setUploading] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [analysisResult, setAnalysisResult] =
    useState(null);

  // Fetch document types
  const fetchDocumentTypes = async () => {
    try {
      setLoadingTypes(true);

      const response =
        await api.get("/document-types");

      setDocumentTypes(
        response.data?.document_types || []
      );

    } catch (err) {
      console.error(
        "FETCH DOCUMENT TYPES ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        "Failed to fetch document types"
      );

    } finally {
      setLoadingTypes(false);
    }
  };

  // Fetch documents
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError("");

      const response =
        await api.get("/documents");

      const list =
        response.data?.documents;

      if (!Array.isArray(list)) {
        throw new Error(
          "Invalid document data received from server"
        );
      }

      setDocumentList(list);

    } catch (err) {
      console.error(
        "FETCH DOCUMENTS ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        err.message ||
        "Failed to fetch documents"
      );

    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    fetchDocumentTypes();
  }, []);

  const handleFileChange = (e) => {
    const file =
      e.target.files[0];

    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();

    setError("");
    setMessage("");
    setAnalysisResult(null);

    if (!institutionId) {
      setError(
        "Please enter an institution ID."
      );
      return;
    }

    if (!departmentId) {
      setError(
        "Please enter a department ID."
      );
      return;
    }

    if (!documentTypeId) {
      setError(
        "Please select a document type."
      );
      return;
    }

    if (!selectedFile) {
      setError(
        "Please select a document."
      );
      return;
    }

    try {
      setUploading(true);

      const formData =
        new FormData();

      formData.append(
        "institution_id",
        institutionId
      );

      formData.append(
        "department_id",
        departmentId
      );

      formData.append(
        "document_type_id",
        documentTypeId
      );

      formData.append(
        "file",
        selectedFile
      );

      // 1. Upload document
      const uploadResponse =
        await api.post(
          "/documents",
          formData
        );

      const documentId =
        uploadResponse.data
          ?.document?.id;

      if (!documentId) {
        throw new Error(
          "Document uploaded, but document ID was not returned."
        );
      }

      // 2. Analyze document
      const analysisResponse =
        await api.post(
          `/documents/${documentId}/analyze`
        );

      const analysis =
        analysisResponse.data;

      console.log(
        "COMPLETE ANALYSIS RESULT:",
        analysis
      );

      setAnalysisResult(
        analysis
      );

      setMessage(
        `Document uploaded and analyzed successfully. ` +
        `Document ID: ${analysis.document_id}, ` +
        `Audit ID: ${analysis.audit_id}, ` +
        `Compliance Score: ${analysis.compliance_score.toFixed(2)}%`
      );

      // Reset form
      setInstitutionId("");
      setDepartmentId("");
      setDocumentTypeId("");
      setSelectedFile(null);

      const fileInput =
        document.getElementById(
          "documentFile"
        );

      if (fileInput) {
        fileInput.value = "";
      }

      await fetchDocuments();

    } catch (err) {
      console.error(
        "UPLOAD AND ANALYZE DOCUMENT ERROR:",
        err
      );

      setError(
        err.response?.data?.detail ||
        err.message ||
        "Failed to upload and analyze document"
      );

    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="dashboard">

      <button onClick={onBack}>
        ← Back to Dashboard
      </button>

      <h1>
        Documents
      </h1>

      {/* Upload Section */}

      <div className="dashboard-card">

        <h2>
          Upload Document
        </h2>

        <form onSubmit={handleUpload}>

          {/* Institution */}

          <label htmlFor="institutionId">
            Institution ID
          </label>

          <input
            id="institutionId"
            type="number"
            value={institutionId}
            onChange={(e) =>
              setInstitutionId(
                e.target.value
              )
            }
            placeholder="Enter institution ID"
            required
          />

          {/* Department */}

          <label htmlFor="departmentId">
            Department ID
          </label>

          <input
            id="departmentId"
            type="number"
            value={departmentId}
            onChange={(e) =>
              setDepartmentId(
                e.target.value
              )
            }
            placeholder="Enter department ID"
            required
          />

          {/* Document Type */}

          <label htmlFor="documentTypeId">
            Document Type
          </label>

          {loadingTypes ? (
            <p>
              Loading document types...
            </p>
          ) : (
            <select
              id="documentTypeId"
              value={documentTypeId}
              onChange={(e) =>
                setDocumentTypeId(
                  e.target.value
                )
              }
              required
            >

              <option value="">
                Select Document Type
              </option>

              {documentTypes.map(
                (type) => (
                  <option
                    key={type.id}
                    value={type.id}
                  >
                    {type.name}
                  </option>
                )
              )}

            </select>
          )}

          {/* File */}

          <label htmlFor="documentFile">
            Select Document
          </label>

          <input
            id="documentFile"
            type="file"
            accept=".pdf"
            onChange={
              handleFileChange
            }
            required
          />

          {selectedFile && (
            <p>
              Selected file:{" "}
              <strong>
                {selectedFile.name}
              </strong>
            </p>
          )}

          <button
            type="submit"
            disabled={
              uploading ||
              loadingTypes
            }
          >
            {uploading
              ? "Uploading and Analyzing..."
              : "Upload Document"}
          </button>

        </form>

        {/* Success */}

        {message && (
          <p
            style={{
              color: "green"
            }}
          >
            {message}
          </p>
        )}

        {/* Error */}

        {error && (
          <p
            style={{
              color: "red"
            }}
          >
            {error}
          </p>
        )}

      </div>

      {/* Analysis Result */}

      {analysisResult && (
        <div className="dashboard-card">

          <h2>
            Document Analysis Result
          </h2>

          <p>
            <strong>
              Document:
            </strong>{" "}
            {analysisResult.document_name}
          </p>

          <p>
            <strong>
              Document ID:
            </strong>{" "}
            {analysisResult.document_id}
          </p>

          <p>
            <strong>
              Institution ID:
            </strong>{" "}
            {analysisResult.institution_id}
          </p>

          <p>
            <strong>
              Audit ID:
            </strong>{" "}
            {analysisResult.audit_id}
          </p>

          <div className="score-card">

            <h3>
              Compliance Score
            </h3>

            <div className="score-value">
              {analysisResult.compliance_score.toFixed(2)}%
            </div>

            <p>
              {analysisResult.compliant_requirements}{" "}
              of{" "}
              {analysisResult.requirements_checked}{" "}
              requirements compliant
            </p>

          </div>

          <h3>
            Compliance Results
          </h3>

          {analysisResult.compliance_results &&
            analysisResult.compliance_results.map(
              (result) => (
                <div
                  className="compliance-result"
                  key={result.check_id}
                >

                  <h4>
                    {result.status ===
                    "Compliant"
                      ? "✓ Compliant"
                      : "✗ Non-Compliant"}
                  </h4>

                  <p>
                    <strong>
                      Check ID:
                    </strong>{" "}
                    {result.check_id}
                  </p>

                  <p>
                    <strong>
                      Requirement ID:
                    </strong>{" "}
                    {result.requirement_id}
                  </p>

                  <p>
                    <strong>
                      Compliance Code:
                    </strong>{" "}
                    {result.compliance_code}
                  </p>

                  <p>
                    <strong>
                      Requirement:
                    </strong>{" "}
                    {result.requirement}
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

          <h3>
            Audit Findings
          </h3>

          {analysisResult.findings &&
          analysisResult.findings.length > 0 ? (
            analysisResult.findings.map(
              (finding) => (
                <div
                  className="compliance-result"
                  key={finding.id}
                >

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
              )
            )
          ) : (
            <p>
              No audit findings.
            </p>
          )}

          <div className="report-info">

            <h3>
              Audit Report
            </h3>

            <p>
              <strong>
                Report ID:
              </strong>{" "}
              {analysisResult.report_id ??
                "Not available"}
            </p>

            <p>
              <strong>
                Report Name:
              </strong>{" "}
              {analysisResult.report_name ??
                "Not available"}
            </p>

            <p>
              <strong>
                Report Path:
              </strong>{" "}
              {analysisResult.report_path ??
                "Not available"}
            </p>

          </div>

        </div>
      )}

      {/* Existing Documents */}

      <h2>
        Existing Documents
      </h2>

      {loading && (
        <p>
          Loading documents...
        </p>
      )}

      {!loading &&
        !error &&
        documentList.length === 0 && (
          <p>
            No documents found.
          </p>
        )}

      {!loading &&
        documentList.length > 0 && (
          <div className="dashboard-cards">

            {documentList.map(
              (document) => (
                <div
                  className="dashboard-card"
                  key={document.id}
                >

                  <h2>
                    {document.file_name}
                  </h2>

                  <p>
                    <strong>
                      Document ID:
                    </strong>{" "}
                    {document.id}
                  </p>

                  <p>
                    <strong>
                      Institution ID:
                    </strong>{" "}
                    {document.institution_id}
                  </p>

                  <p>
                    <strong>
                      Department ID:
                    </strong>{" "}
                    {document.department_id ??
                      "Not assigned"}
                  </p>

                  <p>
                    <strong>
                      Document Type ID:
                    </strong>{" "}
                    {document.document_type_id ??
                      "Not assigned"}
                  </p>

                  <p>
                    <strong>
                      File Path:
                    </strong>{" "}
                    {document.file_path}
                  </p>

                  <p>
                    <strong>
                      Uploaded At:
                    </strong>{" "}
                    {document.uploaded_at ||
                      "Not available"}
                  </p>

                </div>
              )
            )}

          </div>
        )}

    </div>
  );
}

export default Documents;