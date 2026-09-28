import React from "react";

function StatusBadge({ status }) {
  const cleanStatus = status || "PENDING";
  let icon = "⏳";
  if (cleanStatus === "ACCEPTED" || cleanStatus === "PASS") {
    icon = "✓";
  } else if (cleanStatus === "REJECTED" || cleanStatus === "FAIL") {
    icon = "✗";
  }

  return (
    <span className={`status-badge badge-${cleanStatus}`}>
      <span>{icon}</span>
      <span>{cleanStatus}</span>
    </span>
  );
}

export default StatusBadge;
