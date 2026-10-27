import React from "react";

// Loading and error states, used by every page that fetches data.
export function Loading({ what = "Loading" }) {
  return <p className="muted" role="status">{what}…</p>;
}

export function ErrorBox({ message }) {
  if (!message) return null;
  return <div className="error-box" role="alert">{message}</div>;
}

export function InfoBox({ children }) {
  return <div className="info-box">{children}</div>;
}
