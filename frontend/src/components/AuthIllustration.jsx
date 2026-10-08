import React from "react";

function AuthIllustration() {
  return (
    <div style={{ width: "100%", maxWidth: "420px", margin: "0 auto" }}>
      <svg
        viewBox="0 0 500 420"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: "100%", height: "auto", filter: "drop-shadow(0 12px 24px rgba(15, 23, 42, 0.2))" }}
      >
        <defs>
          <linearGradient id="skyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#1e3a8a" stopOpacity="0.95" />
            <stop offset="50%" stopColor="#1e40af" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#0f172a" stopOpacity="0.95" />
          </linearGradient>
          <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#059669" />
          </linearGradient>
          <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fbbf24" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
          <linearGradient id="docGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#f8fafc" />
          </linearGradient>
        </defs>

        {/* Ambient background disc */}
        <circle cx="250" cy="210" r="180" fill="url(#skyGrad)" opacity="0.12" />
        <circle cx="250" cy="210" r="140" fill="#2563eb" opacity="0.08" />

        {/* College Building / Campus Pillars */}
        <g id="campus">
          {/* Base Steps */}
          <rect x="90" y="310" width="320" height="12" rx="3" fill="#cbd5e1" />
          <rect x="105" y="298" width="290" height="12" rx="2" fill="#94a3b8" />
          <rect x="120" y="286" width="260" height="12" rx="2" fill="#64748b" />

          {/* Pillars */}
          <rect x="140" y="160" width="22" height="126" rx="3" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
          <rect x="195" y="160" width="22" height="126" rx="3" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
          <rect x="250" y="160" width="22" height="126" rx="3" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
          <rect x="305" y="160" width="22" height="126" rx="3" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />
          <rect x="360" y="160" width="22" height="126" rx="3" fill="#e2e8f0" stroke="#94a3b8" strokeWidth="2" />

          {/* Architrave Beam */}
          <rect x="125" y="148" width="270" height="14" rx="2" fill="#cbd5e1" stroke="#64748b" strokeWidth="1.5" />

          {/* Pediment / Triangular Roof */}
          <polygon points="260,80 120,148 400,148" fill="#e2e8f0" stroke="#64748b" strokeWidth="2" />
          {/* Pediment Center Medallion */}
          <circle cx="260" cy="124" r="14" fill="url(#goldGrad)" />
          <text x="260" y="129" textAnchor="middle" fill="#ffffff" fontSize="13" fontWeight="bold">★</text>
        </g>

        {/* Floating Verified Document Card */}
        <g id="document-card" transform="translate(180, 150)">
          <rect x="0" y="0" width="160" height="190" rx="10" fill="url(#docGrad)" stroke="#3b82f6" strokeWidth="2" filter="drop-shadow(0 10px 15px rgba(0,0,0,0.15))" />
          {/* Header band */}
          <rect x="15" y="16" width="130" height="8" rx="4" fill="#3b82f6" />
          <rect x="15" y="32" width="90" height="6" rx="3" fill="#93c5fd" />
          
          {/* Structural text lines (simulating PDF sections) */}
          <rect x="15" y="52" width="130" height="4" rx="2" fill="#e2e8f0" />
          <rect x="15" y="64" width="115" height="4" rx="2" fill="#e2e8f0" />
          <rect x="15" y="76" width="125" height="4" rx="2" fill="#e2e8f0" />

          {/* Part A Section Badge */}
          <rect x="15" y="92" width="45" height="14" rx="4" fill="#eff6ff" stroke="#bfdbfe" />
          <text x="37" y="102" textAnchor="middle" fill="#2563eb" fontSize="8" fontWeight="700">PART A</text>
          <rect x="15" y="112" width="130" height="4" rx="2" fill="#e2e8f0" />
          <rect x="15" y="122" width="120" height="4" rx="2" fill="#e2e8f0" />

          {/* Part B Section Badge */}
          <rect x="15" y="136" width="45" height="14" rx="4" fill="#eff6ff" stroke="#bfdbfe" />
          <text x="37" y="146" textAnchor="middle" fill="#2563eb" fontSize="8" fontWeight="700">PART B</text>
          <rect x="15" y="156" width="130" height="4" rx="2" fill="#e2e8f0" />
          <rect x="15" y="166" width="105" height="4" rx="2" fill="#e2e8f0" />

          {/* Verified Badge Checkmark */}
          <circle cx="140" cy="170" r="18" fill="url(#shieldGrad)" stroke="#ffffff" strokeWidth="2.5" />
          <path d="M134 170 L138 174 L147 165" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </g>

        {/* Floating Academic Cap Badge */}
        <g id="grad-cap" transform="translate(60, 110)">
          <rect x="0" y="0" width="80" height="70" rx="12" fill="#ffffff" stroke="#e2e8f0" strokeWidth="1.5" filter="drop-shadow(0 6px 12px rgba(0,0,0,0.08))" />
          <text x="40" y="44" textAnchor="middle" fontSize="30">🎓</text>
          <text x="40" y="60" textAnchor="middle" fill="#0f172a" fontSize="8" fontWeight="700">ACADEMIC</text>
        </g>

        {/* Floating Compliance Shield Badge */}
        <g id="compliance-shield" transform="translate(360, 70)">
          <rect x="0" y="0" width="85" height="74" rx="12" fill="#ffffff" stroke="#e2e8f0" strokeWidth="1.5" filter="drop-shadow(0 6px 12px rgba(0,0,0,0.08))" />
          <text x="42" y="44" textAnchor="middle" fontSize="28">🛡️</text>
          <text x="42" y="62" textAnchor="middle" fill="#059669" fontSize="8" fontWeight="700">100% AUDIT</text>
        </g>
      </svg>
    </div>
  );
}

export default AuthIllustration;
