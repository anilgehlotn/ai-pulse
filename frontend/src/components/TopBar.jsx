import React from "react";

export default function TopBar({ user, org, onSwitchOrg, onLogOut }) {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <span className="brand">AI Pulse</span>
        {org && <span className="topbar-org">{org.org_name}</span>}
        <div className="topbar-right">
          <span className="topbar-user">{user.name}</span>
          {user.organizations.length > 1 && org && (
            <button type="button" className="secondary small-button" onClick={onSwitchOrg}>Switch organization</button>
          )}
          <button type="button" className="secondary small-button" onClick={onLogOut}>Log out</button>
        </div>
      </div>
    </header>
  );
}
