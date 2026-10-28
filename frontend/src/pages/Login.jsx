import React, { useState } from "react";
import { api } from "../api.js";
import { ErrorBox, InfoBox } from "../components/Status.jsx";
import BrandMark from "../components/BrandMark.jsx";

// Seeded by backend/app/seed.py. Listed in development builds, and in production builds made with
// VITE_SHOW_DEMO_ACCOUNTS=true (the public demo only, never a real client deployment).
const DEMO_ACCOUNTS = [
  ["asha@northwind.test", "Admin, Northwind Logistics"],
  ["ravi@consult.test", "Admin at Bluepeak Retail, employee at Northwind (two organizations)"],
  ["rohan@northwind.test", "Employee, Sales: uses AI a lot, low safety"],
  ["priya@northwind.test", "Employee, Support: partly answered"],
  ["farah@northwind.test", "Employee, Sales: not assessed yet"],
  ["meera@bluepeak.test", "Admin, Bluepeak Retail"],
  ["reviewer@northwind.test", "Reviewer: human review queue"],
];
const DEMO_PASSWORD = "pulse123";

// Read on every render, not once at import, so tests can change the flags.
function showDemoAccounts() {
  return import.meta.env.DEV || import.meta.env.VITE_SHOW_DEMO_ACCOUNTS === "true";
}

export default function Login({ notice, onLoggedIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLoggedIn(await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }));
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="narrow stack">
      <form className="card stack auth-card" onSubmit={submit}>
        <BrandMark />
        <div>
          <h1>Sign in to AI Pulse</h1>
          <p className="muted">See how your team uses AI, and how safely.</p>
        </div>
        {notice && <InfoBox>{notice}</InfoBox>}
        <div className="field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="username" required value={email}
                 onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" required value={password}
                 onChange={(e) => setPassword(e.target.value)} />
        </div>
        <ErrorBox message={error} />
        <button type="submit" className="wide" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
      </form>

      {showDemoAccounts() && (
        <aside className="card demo stack" aria-labelledby="demo-title">
          <h2 id="demo-title">Demo accounts</h2>
          <p className="muted small">For trying the app. Every password is <code>{DEMO_PASSWORD}</code>.</p>
          <ul className="plain-list">
            {DEMO_ACCOUNTS.map(([demoEmail, role]) => (
              <li key={demoEmail}>
                <button type="button" className="link"
                        onClick={() => { setEmail(demoEmail); setPassword(DEMO_PASSWORD); }}>
                  {demoEmail}
                </button>
                <span className="muted small"> {role}</span>
              </li>
            ))}
          </ul>
        </aside>
      )}
    </div>
  );
}
