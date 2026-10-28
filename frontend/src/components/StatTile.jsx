import React from "react";

// One KPI tile: label top-left, icon top-right, value bottom-left, a small visual bottom-right.
// The value is shown exactly as the backend sent it. Text values ("fewer than 5", a level) get a smaller size.
export default function StatTile({ label, icon: Icon, value, suffix, visual, highlight = false }) {
  const isText = typeof value === "string";
  return (
    <div className={`stat-tile ${highlight ? "stat-tile-highlight" : ""}`}>
      <div className="stat-tile-top">
        <span className="stat-label">{label}</span>
        {Icon && <span className="icon-chip" aria-hidden="true"><Icon size={18} /></span>}
      </div>
      <div className="stat-tile-bottom">
        <span className={isText ? "stat-value stat-value-text" : "stat-value"}>
          {value}
          {suffix && <span className="stat-suffix">{suffix}</span>}
        </span>
        {visual}
      </div>
    </div>
  );
}
