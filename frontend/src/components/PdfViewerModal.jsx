import React, { useState, useEffect } from "react";
import api from "../api";

function PdfViewerModal({ isOpen, onClose, documentId, fileName, isAccepted, canDownload, onDownload }) {
  const [blobUrl, setBlobUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !documentId) {
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setBlobUrl(null);
      }
      return;
    }

    let isMounted = true;
    setLoading(true);
    setError(null);

    // Fetch the PDF as a blob using authenticated Axios client
    api.get(`/documents/${documentId}/view`, { responseType: "blob" })
      .then((res) => {
        if (!isMounted) return;
        const pdfBlob = new Blob([res.data], { type: "application/pdf" });
        const objectUrl = URL.createObjectURL(pdfBlob);
        setBlobUrl(objectUrl);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setLoading(false);
        const errMsg = err.response?.data?.detail || "Failed to load document PDF. Please verify permissions.";
        setError(errMsg);
      });

    return () => {
      isMounted = false;
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
      }
    };
  }, [isOpen, documentId]);

  if (!isOpen || !documentId) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" style={{ maxWidth: "950px", height: "88vh" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>PDF Document Viewer</h3>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
              {fileName || `Document #${documentId}`}
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="modal-body" style={{ padding: "0", height: "calc(100% - 130px)", background: "#1a1f2c", position: "relative" }}>
          {loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", color: "#cbd5e1" }}>
              <div className="spinner" style={{ width: "36px", height: "36px", border: "3px solid rgba(255,255,255,0.2)", borderTopColor: "var(--primary)", borderRadius: "50%", animation: "spin 0.8s linear infinite" }}></div>
              <p style={{ marginTop: "12px", fontSize: "14px" }}>Loading institutional document securely...</p>
            </div>
          )}

          {error && !loading && (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", padding: "24px", textAlign: "center" }}>
              <div style={{ fontSize: "40px", marginBottom: "12px" }}>🔒</div>
              <h4 style={{ color: "#ef4444", marginBottom: "8px" }}>Access Restricted</h4>
              <p style={{ color: "#94a3b8", maxWidth: "420px", fontSize: "14px" }}>{error}</p>
            </div>
          )}

          {!loading && !error && blobUrl && (
            <iframe
              src={blobUrl}
              title={fileName}
              width="100%"
              height="100%"
              style={{ border: "none" }}
            />
          )}
        </div>

        <div className="modal-footer" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            {isAccepted ? (
              <span className="badge badge-success" style={{ fontSize: "12px", padding: "4px 10px" }}>
                ✓ Official Accepted Document
              </span>
            ) : (
              <span className="badge badge-warning" style={{ fontSize: "12px", padding: "4px 10px" }}>
                ⚠️ Download locked until document is formally Accepted
              </span>
            )}
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            {isAccepted && canDownload && (
              <button 
                className="btn btn-success" 
                onClick={() => {
                  if (onDownload) {
                    onDownload(documentId, fileName);
                  } else if (blobUrl) {
                    const link = document.createElement("a");
                    link.href = blobUrl;
                    link.download = fileName || `document_${documentId}.pdf`;
                    link.click();
                  }
                }}
              >
                📥 Download Accepted PDF
              </button>
            )}
            {blobUrl && (
              <a
                href={blobUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
              >
                ↗ Open in Full Screen
              </a>
            )}
            <button className="btn btn-secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PdfViewerModal;
