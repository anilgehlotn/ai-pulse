import React from "react";
import { ChevronRight } from "lucide-react";
import { ROLE_LABELS } from "../labels.js";
import { ErrorBox, Loading } from "../components/Status.jsx";
import Badge from "../components/Badge.jsx";
import BrandMark from "../components/BrandMark.jsx";

export default function OrgPicker({ organizations, busy, error, onPick }) {
  return (
    <div className="narrow card stack auth-card">
      <BrandMark />
      <div>
        <h1>Choose an organization</h1>
        <p className="muted">You belong to more than one. You can switch later from the top bar.</p>
      </div>
      <ul className="org-list">
        {organizations.map((o) => (
          <li key={o.org_id}>
            <button type="button" className="org-button" disabled={busy} onClick={() => onPick(o)}>
              <span className="org-name">{o.org_name}</span>
              <Badge>{ROLE_LABELS[o.role]}</Badge>
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
      {busy && <Loading what="Opening" />}
      <ErrorBox message={error} />
    </div>
  );
}
