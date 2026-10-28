import React from "react";
import { Info, TriangleAlert } from "lucide-react";

// Loading and error states, used by every page that fetches data.
export function Loading({ what = "Loading" }) {
  return <p className="muted loading" role="status">{what}…</p>;
}

export function ErrorBox({ message }) {
  if (!message) return null;
  return (
    <div className="box box-error" role="alert">
      <TriangleAlert size={18} aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}

export function InfoBox({ children }) {
  return (
    <div className="box box-info">
      <Info size={18} aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
