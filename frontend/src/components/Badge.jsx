import React from "react";

// A pill-shaped text label. The tone only adds colour: the text always says what it means.
export default function Badge({ children, tone = "neutral", size }) {
  return <span className={`badge badge-${tone} ${size === "large" ? "badge-large" : ""}`}>{children}</span>;
}

const QUADRANT_TONES = { Leading: "good", Exposed: "warn", Cautious: "info", "Getting started": "neutral" };

export function QuadrantBadge({ quadrant }) {
  if (!quadrant) return null;
  return <Badge tone={QUADRANT_TONES[quadrant]}>{quadrant}</Badge>;
}

const PRIVACY_LABELS = { shown: "Shown", merged: "Merged", hidden: "Hidden" };
const PRIVACY_TONES = { shown: "good", merged: "info", hidden: "neutral" };

export function PrivacyBadge({ privacy }) {
  return <Badge tone={PRIVACY_TONES[privacy]}>{PRIVACY_LABELS[privacy]}</Badge>;
}
