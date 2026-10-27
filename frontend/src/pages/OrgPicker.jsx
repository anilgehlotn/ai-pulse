import React from "react";
import { ErrorBox, Loading } from "../components/Status.jsx";

export default function OrgPicker({ organizations, busy, error, onPick }) {
  return (
    <div className="narrow card stack">
      <h1>Choose an organization</h1>
      <p className="muted">You belong to more than one. You can switch later from the top bar.</p>
      <ul className="org-list">
        {organizations.map((o) => (
          <li key={o.org_id}>
            <button type="button" className="org-button" disabled={busy} onClick={() => onPick(o)}>
              <span>{o.org_name}</span>
              <span className="muted small">{o.role === "admin" ? "Admin" : "Employee"}</span>
            </button>
          </li>
        ))}
      </ul>
      {busy && <Loading what="Opening" />}
      <ErrorBox message={error} />
    </div>
  );
}
