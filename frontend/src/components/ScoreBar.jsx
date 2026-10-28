import React from "react";
import { hasValue } from "../labels.js";

// A small bar on the 1-5 scale, with a mark at 3 (the quadrant line). Decorative: the number is always
// written next to it, so screen readers skip it.
export default function ScoreBar({ value }) {
  const percent = hasValue(value) ? ((value - 1) / 4) * 100 : 0; // position only, never displayed
  return (
    <div className="score-bar" aria-hidden="true">
      {hasValue(value) && <div className="score-bar-fill" style={{ width: `${percent}%` }} />}
      <div className="score-bar-threshold" />
    </div>
  );
}

// Five ticks for 1-5 with a dot where the value sits.
export function ScaleMarker({ value }) {
  if (!hasValue(value)) return null;
  const percent = ((value - 1) / 4) * 100; // position only, never displayed
  return (
    <div className="scale-marker" aria-hidden="true">
      <div className="scale-marker-line">
        <span className="scale-marker-dot" style={{ left: `${percent}%` }} />
      </div>
      <div className="scale-marker-ends"><span>1</span><span>5</span></div>
    </div>
  );
}
