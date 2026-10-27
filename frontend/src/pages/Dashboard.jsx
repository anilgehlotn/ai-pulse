import React from "react";
import { useApi } from "../useApi.js";
import { RISK_FOR_TEAMS, riskText, show } from "../labels.js";
import { ErrorBox, InfoBox, Loading } from "../components/Status.jsx";
import Badge, { PrivacyBadge, QuadrantBadge } from "../components/Badge.jsx";
import QuadrantChart from "../components/QuadrantChart.jsx";

// Every number on this page comes straight from /dashboard, which applies the anonymity rule.
// Nothing here adds, subtracts or averages anything.
export default function Dashboard() {
  const { data, error, loading } = useApi("/dashboard");

  if (loading) return <Loading what="Loading the dashboard" />;
  if (error) return <ErrorBox message={error} />;

  const published = data.groups.filter((g) => g.privacy !== "hidden");
  return (
    <div className="stack">
      <header className="page-head">
        <h1>{data.organization}</h1>
        <p className="muted">
          Teams with fewer than {data.min_group_size} respondents are merged into Other teams or hidden,
          so no individual can be identified.
        </p>
      </header>

      <Overall overall={data.overall} />
      <ActFirst rows={data.act_first} />

      <section className="card" aria-labelledby="chart-title">
        <h2 id="chart-title">Adoption vs safety</h2>
        <p className="muted">
          How much each team uses AI, against how safely. Teams in the bottom-right corner use AI a lot
          without the safeguards.
        </p>
        <QuadrantChart groups={published} />
      </section>

      <TeamTable groups={data.groups} />
    </div>
  );
}

function Overall({ overall }) {
  return (
    <section className="card" aria-labelledby="overall-title">
      <h2 id="overall-title">Whole organization</h2>
      {overall.privacy === "hidden" ? (
        <InfoBox>{overall.reason}</InfoBox>
      ) : (
        <>
          <dl className="stats">
            <div><dt>Respondents</dt><dd>{overall.respondents}</dd></div>
            <div><dt>Average score</dt><dd>{show(overall.average_score)}</dd></div>
            <div><dt>Level</dt><dd><Badge tone="accent">{overall.level}</Badge></dd></div>
            <div><dt>Awaiting human review</dt><dd><span>{overall.awaiting_review}</span></dd></div>
          </dl>
          <h3>Top risks</h3>
          <ul className="risk-list">
            {overall.top_risks.map((r) => (
              <li key={r.risk}>
                <span>{riskText(RISK_FOR_TEAMS, r.risk)}</span>
                <span className="risk-people"><span>{r.people}</span> {r.people === 1 ? "person" : "people"}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function ActFirst({ rows }) {
  if (rows.length === 0) return null;
  return (
    <section className="callout" aria-labelledby="act-first-title">
      <h2 id="act-first-title">Act first</h2>
      <p>These teams use AI a lot but their safety habits are low. Start safety training here.</p>
      <ul>
        {rows.map((row) => (
          <li key={row.name}><strong>{row.name}</strong>: {row.reason}</li>
        ))}
      </ul>
    </section>
  );
}

function TeamTable({ groups }) {
  return (
    <section className="card" aria-labelledby="teams-title">
      <h2 id="teams-title">Teams</h2>
      <div className="table-scroll">
        <table aria-labelledby="teams-title">
          <thead>
            <tr>
              <th scope="col">Team</th><th scope="col">Privacy</th><th scope="col">Employees</th>
              <th scope="col">Respondents</th><th scope="col">Average</th><th scope="col">Level</th>
              <th scope="col">Adoption</th><th scope="col">Safety</th><th scope="col">Quadrant</th>
            </tr>
          </thead>
          <tbody>
            {groups.map((g) => (g.privacy === "hidden" ? (
              <tr key={g.name}>
                <th scope="row">{g.name}</th>
                <td><PrivacyBadge privacy={g.privacy} /></td>
                <td colSpan={7} className="muted">{g.message}</td>
              </tr>
            ) : (
              <tr key={g.name}>
                <th scope="row">{g.name}</th>
                <td>
                  <PrivacyBadge privacy={g.privacy} />
                  {g.teams && <div className="muted small">includes: {g.teams.join(", ")}</div>}
                </td>
                <td>{g.employees}</td>
                <td>{g.respondents}</td>
                <td>{show(g.average_score)}</td>
                <td>{g.level}</td>
                <td>{show(g.adoption)}</td>
                <td>{show(g.safety)}</td>
                <td>{g.quadrant ? <QuadrantBadge quadrant={g.quadrant} /> : show(g.quadrant)}</td>
              </tr>
            )))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
