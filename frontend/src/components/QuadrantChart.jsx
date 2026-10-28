import React from "react";
import { show } from "../labels.js";

// Adoption (x) against safety (y), both on the 1-5 scale, with lines at 3.
// SVG units; the drawing scales to fit its container.
const PLOT = 340;      // the square plotting area
const LEFT = 56;       // room for the safety axis label and ticks
const BOTTOM = 52;     // room for the adoption axis label and ticks
const EDGE = 16;       // small margin on the top and right
const WIDTH = LEFT + PLOT + EDGE;
const HEIGHT = EDGE + PLOT + BOTTOM;
const THRESHOLD = 3;   // same as QUADRANT_THRESHOLD in the backend

// A score of 1 sits on the left/bottom edge, 5 on the right/top edge.
const x = (score) => LEFT + ((score - 1) / 4) * PLOT;
const y = (score) => EDGE + PLOT - ((score - 1) / 4) * PLOT;

const TICKS = [1, 2, 3, 4, 5];

export default function QuadrantChart({ groups }) {
  const placed = groups.filter((g) => g.adoption !== null && g.adoption !== undefined
    && g.safety !== null && g.safety !== undefined);

  if (placed.length === 0) {
    return <p className="muted">No team has enough answers on both axes to be placed yet.</p>;
  }

  return (
    <figure className="quadrant">
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-labelledby="quadrant-title quadrant-desc">
        <title id="quadrant-title">Adoption vs safety by team</title>
        <desc id="quadrant-desc">
          Each published team is a dot. Further right means more AI use, higher up means safer habits.
          The same data is in the table below the chart.
        </desc>

        {/* The risky corner is tinted, and also labelled in words. */}
        <rect className="q-frame" x={x(1)} y={y(5)} width={PLOT} height={PLOT} />
        <rect className="q-exposed" x={x(THRESHOLD)} y={y(THRESHOLD)} width={x(5) - x(THRESHOLD)} height={y(1) - y(THRESHOLD)} />

        {TICKS.map((t) => (
          <g key={t} className="q-tick">
            <line className="q-grid" x1={x(t)} y1={y(5)} x2={x(t)} y2={y(1)} />
            <line className="q-grid" x1={x(1)} y1={y(t)} x2={x(5)} y2={y(t)} />
            <text x={x(t)} y={y(1) + 20} textAnchor="middle">{t}</text>
            <text x={x(1) - 12} y={y(t) + 4} textAnchor="end">{t}</text>
          </g>
        ))}
        <line className="q-line" x1={x(THRESHOLD)} y1={y(5)} x2={x(THRESHOLD)} y2={y(1)} />
        <line className="q-line" x1={x(1)} y1={y(THRESHOLD)} x2={x(5)} y2={y(THRESHOLD)} />

        <text className="q-corner" x={x(1) + 10} y={y(5) + 22}>Cautious</text>
        <text className="q-corner" x={x(5) - 10} y={y(5) + 22} textAnchor="end">Leading</text>
        <text className="q-corner" x={x(1) + 10} y={y(1) - 12}>Getting started</text>
        <text className="q-corner q-corner-warn" x={x(5) - 10} y={y(1) - 12} textAnchor="end">Exposed</text>

        <text className="q-axis" x={x(3)} y={HEIGHT - 8} textAnchor="middle">Adoption: how much AI is used</text>
        <text className="q-axis" transform={`translate(16 ${y(3)}) rotate(-90)`} textAnchor="middle">
          Safety: how safely it is used
        </text>

        {placed.map((g) => (
          <g key={g.name} className="q-dot">
            <circle cx={x(g.adoption)} cy={y(g.safety)} r="7" />
            <text x={x(g.adoption) + 12} y={y(g.safety) + 4}>{g.name}</text>
          </g>
        ))}
      </svg>

      {/* Tables ignore a 1px width, so the wrapper is what gets visually hidden. */}
      <div className="visually-hidden">
      <table>
        <caption>Adoption and safety by team</caption>
        <thead>
          <tr><th scope="col">Team</th><th scope="col">Adoption</th><th scope="col">Safety</th><th scope="col">Quadrant</th></tr>
        </thead>
        <tbody>
          {placed.map((g) => (
            <tr key={g.name}>
              <th scope="row">{g.name}</th><td>{g.adoption}</td><td>{g.safety}</td><td>{show(g.quadrant)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </figure>
  );
}
