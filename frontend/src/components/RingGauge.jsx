import React from "react";
import { hasValue, show } from "../labels.js";

// A ring for a score on the 1-5 scale. The number in the middle is the backend value, unchanged.
// pathLength="100" lets the arc length be a plain percentage. A score of 1 is an empty ring, 5 a full one.
export default function RingGauge({ value, label }) {
  const clamped = hasValue(value) ? Math.min(5, Math.max(1, value)) : 1;
  const percent = ((clamped - 1) / 4) * 100; // geometry only, never displayed

  return (
    <figure className="ring">
      <svg viewBox="0 0 120 120" role="img" aria-label={`${label}: ${hasValue(value) ? `${value} out of 5` : "not enough answers yet"}`}>
        <circle className="ring-track" cx="60" cy="60" r="50" />
        {hasValue(value) && (
          <circle
            className="ring-arc"
            cx="60" cy="60" r="50"
            pathLength="100"
            strokeDasharray={`${percent} 100`}
            transform="rotate(-90 60 60)"
          />
        )}
      </svg>
      <div className="ring-center" aria-hidden="true">
        <span className="ring-value">{show(value)}</span>
        <span className="ring-max">out of 5</span>
      </div>
    </figure>
  );
}
