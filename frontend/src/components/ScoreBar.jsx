import React from "react";

// A labelled horizontal bar on the 1-5 scale. The number is always written next to the bar.
export default function ScoreBar({ label, value, hint }) {
  const hasValue = value !== null && value !== undefined;
  const percent = hasValue ? ((value - 1) / 4) * 100 : 0; // position only, never displayed
  return (
    <div className="score-bar">
      <div className="score-bar-head">
        <span className="score-bar-label">{label}</span>
        <span className="score-bar-value">{hasValue ? `${value} / 5` : "Not enough answers yet"}</span>
      </div>
      <div className="score-bar-track" aria-hidden="true">
        {hasValue && <div className="score-bar-fill" style={{ width: `${percent}%` }} />}
        <div className="score-bar-threshold" />
      </div>
      {hint && <p className="muted small">{hint}</p>}
    </div>
  );
}
