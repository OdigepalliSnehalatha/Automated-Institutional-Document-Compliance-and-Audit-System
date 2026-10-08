import React from "react";

function InstitutionLogo({ logoUrl, size = 40, className = "" }) {
  if (logoUrl) {
    return (
      <img
        src={logoUrl}
        alt="Institution Logo"
        style={{
          width: `${size}px`,
          height: `${size}px`,
          objectFit: "contain",
          borderRadius: "8px",
        }}
        className={className}
      />
    );
  }

  // Fallback to high-quality institutional collegiate vector crest
  return (
    <div
      style={{
        width: `${size}px`,
        height: `${size}px`,
        minWidth: `${size}px`,
        minHeight: `${size}px`,
        borderRadius: "10px",
        background: "linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#ffffff",
        boxShadow: "0 2px 8px rgba(30, 58, 138, 0.35)",
        fontSize: `${Math.round(size * 0.52)}px`,
        userSelect: "none",
      }}
      className={className}
      title="Institutional Emblem"
    >
      🏛️
    </div>
  );
}

export default InstitutionLogo;
