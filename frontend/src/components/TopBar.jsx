import React from "react";
import { ArrowLeftRight, LogOut } from "lucide-react";
import { ROLE_LABELS } from "../labels.js";
import Avatar from "./Avatar.jsx";
import BrandMark from "./BrandMark.jsx";

// One header row: brand, the tabs (passed in as nav), then the organization and the user.
export default function TopBar({ user, org, nav, onSwitchOrg, onLogOut }) {
  return (
    <header className="topbar">
      <BrandMark />
      {nav}
      <div className="topbar-right">
        {org && <span className="topbar-org">{org.org_name}</span>}
        {user.organizations.length > 1 && org && (
          <button type="button" className="pill-button" onClick={onSwitchOrg}>
            <ArrowLeftRight size={16} aria-hidden="true" />
            <span className="pill-label">Switch organization</span>
          </button>
        )}
        <Avatar name={user.name} role={org && ROLE_LABELS[org.role]} />
        <button type="button" className="pill-button quiet" onClick={onLogOut}>
          <LogOut size={16} aria-hidden="true" />
          <span className="pill-label">Log out</span>
        </button>
      </div>
    </header>
  );
}
