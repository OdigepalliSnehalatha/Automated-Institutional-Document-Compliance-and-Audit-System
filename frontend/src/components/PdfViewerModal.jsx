import React from "react";

function PdfViewerModal({ isOpen, onClose, documentId, fileName, isAccepted, canDownload, onDownload }) {
  if (!isOpen || !documentId) return null;

  const pdfUrl = `http://localhost:8000/documents/${documentId}/view`;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" style={{ maxWidth: "900px", height: "85vh" }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>PDF Document Viewer</h3>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "2px" }}>
              {fileName}
            </p>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body" style={{ padding: "0", height: "calc(100% - 130px)" }}>
          <iframe
            src={pdfUrl}
            title={fileName}
            width="100%"
            height="100%"
            style={{ border: "none" }}
          />
        </div>

        <div className="modal-footer">
          {isAccepted && canDownload && (
            <button className="btn btn-success" onClick={() => onDownload(documentId, fileName)}>
              📥 Download Accepted PDF
            </button>
          )}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary"
          >
            ↗ Open in New Tab
          </a>
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default PdfViewerModal;
