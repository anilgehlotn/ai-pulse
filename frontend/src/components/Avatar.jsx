import React from "react";
import { initials } from "../labels.js";

// A circle with the user's initials, then their name and role.
export default function Avatar({ name, role }) {
  return (
    <div className="avatar">
      <span className="avatar-circle" aria-hidden="true">{initials(name)}</span>
      <span className="avatar-text">
        <span className="avatar-name">{name}</span>
        {role && <span className="avatar-role">{role}</span>}
      </span>
    </div>
  );
}
