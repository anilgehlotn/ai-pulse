import React, { useEffect, useState } from "react";
import { api, clearToken, getToken, onSessionExpired, setToken } from "./api.js";
import Login from "./pages/Login.jsx";
import OrgPicker from "./pages/OrgPicker.jsx";
import Diagnostic from "./pages/Diagnostic.jsx";
import Report from "./pages/Report.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import TopBar from "./components/TopBar.jsx";
import Tabs from "./components/Tabs.jsx";
import { ErrorBox, Loading } from "./components/Status.jsx";
import { firstName } from "./labels.js";

const ADMIN_TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "diagnostic", label: "My diagnostic" },
  { id: "report", label: "My report" },
];
const EMPLOYEE_TABS = ADMIN_TABS.slice(1);

// The steps: restoring the session -> login -> pick an organization -> one of the tabs.
export default function App() {
  const [restoring, setRestoring] = useState(Boolean(getToken()));
  const [user, setUser] = useState(null);   // {name, organizations: [{org_id, org_name, role}]}
  const [org, setOrg] = useState(null);     // the selected organization
  const [view, setView] = useState(null);   // "dashboard" | "diagnostic" | "report"
  const [notice, setNotice] = useState(""); // shown on the login page
  const [picking, setPicking] = useState(false);
  const [error, setError] = useState("");

  function signOut(message = "") {
    clearToken();
    setUser(null);
    setOrg(null);
    setView(null);
    setNotice(message);
  }

  // Admins start on the dashboard. Employees start on their report if they have one.
  async function enterOrg(o) {
    setOrg(o);
    setView(null);
    if (o.role === "admin") {
      setView("dashboard");
      return;
    }
    try {
      const report = await api("/reports/me");
      setView(report.answered > 0 ? "report" : "diagnostic");
    } catch {
      setView("diagnostic");
    }
  }

  // Ask the server for a token scoped to this organization.
  async function chooseOrg(o) {
    setPicking(true);
    setError("");
    try {
      const data = await api("/auth/select-org", { method: "POST", body: JSON.stringify({ org_id: o.org_id }) });
      setToken(data.token);
      await enterOrg(o);
    } catch (err) {
      setError(err.message);
    } finally {
      setPicking(false);
    }
  }

  function startSession(me) {
    setUser(me);
    setNotice("");
    if (me.selected_org) enterOrg(me.selected_org);
    else if (me.organizations.length === 1) chooseOrg(me.organizations[0]);
  }

  useEffect(() => {
    onSessionExpired(() => signOut("Your session expired. Please sign in again."));
    // A refresh keeps the token: ask the server who it belongs to and which organization it is for.
    if (getToken()) {
      api("/auth/me")
        .then(startSession)
        .catch((err) => { if (err.status !== 401) signOut(err.message); })
        .finally(() => setRestoring(false));
    }
  }, []);

  function loggedIn(data) {
    setToken(data.token);
    startSession({ name: data.name, organizations: data.organizations, selected_org: null });
  }

  if (restoring) return <div className="shell"><div className="page"><Loading what="Restoring your session" /></div></div>;
  if (!user) return <div className="shell"><div className="page"><Login notice={notice} onLoggedIn={loggedIn} /></div></div>;

  const tabs = org && org.role === "admin" ? ADMIN_TABS : EMPLOYEE_TABS;
  const name = firstName(user.name);
  return (
    <div className="shell">
      <TopBar
        user={user}
        org={org}
        nav={org && view && <Tabs tabs={tabs} current={view} onSelect={setView} />}
        onSwitchOrg={() => { setOrg(null); setView(null); }}
        onLogOut={() => signOut()}
      />
      <div className="page">
        {!org && (
          <OrgPicker organizations={user.organizations} busy={picking} error={error} onPick={chooseOrg} />
        )}
        {org && !view && (error ? <ErrorBox message={error} /> : <Loading what="Opening" />)}
        {org && view && (
          <main key={`${org.org_id}-${view}`}>
            {view === "dashboard" && <Dashboard firstName={name} />}
            {view === "diagnostic" && <Diagnostic onSubmitted={() => setView("report")} />}
            {view === "report" && <Report firstName={name} onTakeDiagnostic={() => setView("diagnostic")} />}
          </main>
        )}
      </div>
    </div>
  );
}
