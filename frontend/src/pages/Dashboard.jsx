import React from "react";
import { Award, CircleCheck, Gauge, Hourglass, Lock, Users } from "lucide-react";
import { useApi } from "../useApi.js";
import { RISK_FOR_TEAMS, riskText, show, today } from "../labels.js";
import { ErrorBox, Loading } from "../components/Status.jsx";
import Badge, { PrivacyBadge, QuadrantBadge } from "../components/Badge.jsx";
import Card from "../components/Card.jsx";
import StatTile from "../components/StatTile.jsx";
import RingGauge from "../components/RingGauge.jsx";
import { ScaleMarker } from "../components/ScoreBar.jsx";
import QuadrantChart from "../components/QuadrantChart.jsx";

// Every number on this page comes straight from /dashboard, which applies the anonymity rule.
// Nothing here adds, subtracts, averages or rounds anything.
export default function Dashboard({ firstName }) {
  const { data, error, loading } = useApi("/dashboard");

  if (loading) return <Loading what="Loading the dashboard" />;
  if (error) return <ErrorBox message={error} />;

  const overall = data.overall;
  const shown = overall.privacy !== "hidden";
  const published = data.groups.filter((g) => g.privacy !== "hidden");
  return (
    <div className="stack">
      <header className="greeting">
        <p className="muted">{today()}</p>
        <h1>Hello, {firstName}</h1>
        <div className="greeting-meta">
          <span className="greeting-org">{data.organization}</span>
          <span className="soft-pill">Teams under {data.min_group_size} people are merged or hidden</span>
        </div>
      </header>

      <section aria-labelledby="overall-title">
        <h2 id="overall-title" className="visually-hidden">Whole organization</h2>
        {shown ? <OverallTiles overall={overall} /> : <HiddenOverall reason={overall.reason} />}
      </section>

      {(shown || data.act_first.length > 0) && (
        <div className="grid-3">
          {shown && (
            <Card id="maturity" title="Maturity">
              <RingGauge value={overall.average_score} label="Average score" />
              <p className="center muted">Level: <strong className="text">{overall.level}</strong></p>
            </Card>
          )}
          <ActFirst rows={data.act_first} />
          {shown && <TopRisks risks={overall.top_risks} />}
        </div>
      )}

      <Card id="chart" title="Adoption vs safety">
        <p className="muted">
          How much each team uses AI, against how safely. Teams in the bottom-right corner use AI a lot
          without the safeguards.
        </p>
        <QuadrantChart groups={published} />
      </Card>

      <TeamTable groups={data.groups} />
    </div>
  );
}

function OverallTiles({ overall }) {
  return (
    <div className="tiles">
      <StatTile label="Respondents" icon={Users} value={overall.respondents} highlight
                visual={<span className="stat-note">people answered</span>} />
      <StatTile label="Average score" icon={Gauge} value={show(overall.average_score)} suffix="/ 5"
                visual={<ScaleMarker value={overall.average_score} />} />
      <StatTile label="Level" icon={Award} value={<Badge tone="accent" size="large">{overall.level}</Badge>} />
      <StatTile label="Awaiting human review" icon={Hourglass} value={overall.awaiting_review}
                visual={<span className="stat-note">answers</span>} />
    </div>
  );
}

// No figures at all: the backend explains why.
function HiddenOverall({ reason }) {
  return (
    <div className="hidden-tile">
      <span className="icon-chip" aria-hidden="true"><Lock size={18} /></span>
      <div>
        <p className="hidden-tile-title">Organization totals are hidden</p>
        <p className="muted">{reason}</p>
      </div>
    </div>
  );
}

function ActFirst({ rows }) {
  return (
    <Card id="act-first" title="Act first" tone="accent">
      {rows.length === 0 ? (
        <p className="calm"><CircleCheck size={20} aria-hidden="true" /> No team needs urgent action.</p>
      ) : (
        <>
          <p>These teams use AI a lot but their safety habits are low. Start safety training here.</p>
          <ul className="plain-list">
            {rows.map((row) => (
              <li key={row.name} className="act-row">
                <strong>{row.name}</strong>
                <span>{row.reason}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}

function TopRisks({ risks }) {
  return (
    <Card id="risks" title="Top risks">
      {risks.length === 0 ? (
        <p className="muted">No risks reported.</p>
      ) : (
        <ul className="plain-list">
          {risks.map((r) => (
            <li key={r.risk} className="risk-row">
              <span>{riskText(RISK_FOR_TEAMS, r.risk)}</span>
              <span className="count-pill"><span>{r.people}</span> {r.people === 1 ? "person" : "people"}</span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

function TeamTable({ groups }) {
  return (
    <Card id="teams" title="Teams">
      <p className="muted small scroll-hint">Scroll the table sideways to see every column.</p>
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
                <th scope="row">
                  {g.name}
                  {g.teams && <div className="muted small">Includes {g.teams.join(", ")}</div>}
                </th>
                <td><PrivacyBadge privacy={g.privacy} /></td>
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
    </Card>
  );
}
