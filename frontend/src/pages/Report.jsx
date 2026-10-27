import React, { useState } from "react";
import { useApi } from "../useApi.js";
import { RISK_FOR_YOU, riskText, show } from "../labels.js";
import { ErrorBox, InfoBox, Loading } from "../components/Status.jsx";
import Badge, { QuadrantBadge } from "../components/Badge.jsx";
import ScoreBar from "../components/ScoreBar.jsx";
import DeleteMyData from "../components/DeleteMyData.jsx";

export default function Report({ onTakeDiagnostic }) {
  const { data, error, loading, reload } = useApi("/reports/me");
  const [deleted, setDeleted] = useState(null);

  if (loading && !data) return <Loading what="Loading your report" />;
  if (error) return <ErrorBox message={error} />;

  function handleDeleted(result) {
    setDeleted(result);
    reload();
  }

  return (
    <div className="stack">
      <header className="page-head">
        <h1>My report</h1>
        <p className="muted">{data.name} · {data.organization}</p>
      </header>

      {deleted && <Deleted result={deleted} />}

      {data.answered === 0 ? (
        <section className="card empty">
          <h2>Not assessed</h2>
          <p>You haven't answered the diagnostic yet. It takes about five minutes.</p>
          <button type="button" onClick={onTakeDiagnostic}>Take the diagnostic</button>
        </section>
      ) : (
        <Results report={data} onRetake={onTakeDiagnostic} onDeleted={handleDeleted} />
      )}
    </div>
  );
}

function Results({ report, onRetake, onDeleted }) {
  const waiting = report.awaiting_review;
  return (
    <>
      <section className="card" aria-labelledby="level-title">
        <h2 id="level-title" className="visually-hidden">Your level</h2>
        <div className="level-row">
          <Badge tone="accent">{report.level}</Badge>
          <span className="big-number">{show(report.average_score)}</span>
          <span className="muted">average on a 1–5 scale</span>
        </div>
        {waiting > 0 && (
          <p className="note">
            {waiting === 1
              ? "1 answer is waiting for a human review and isn't counted yet."
              : `${waiting} answers are waiting for a human review and aren't counted yet.`}
          </p>
        )}
      </section>

      <section className="card" aria-labelledby="axes-title">
        <h2 id="axes-title">How much and how safely you use AI</h2>
        <ScoreBar label="Adoption" value={report.adoption} hint="How often and how deeply you use AI in your work." />
        <ScoreBar label="Safety" value={report.safety} hint="Reviewing output, protecting data and following the policy." />
        <div className="quadrant-summary">
          <QuadrantBadge quadrant={report.quadrant} />
          <p>{report.quadrant_explanation}</p>
        </div>
      </section>

      {report.focus_next && (
        <section className="callout" aria-labelledby="focus-title">
          <h2 id="focus-title">Focus next</h2>
          <p>{report.focus_next.tip}</p>
        </section>
      )}

      <section className="card" aria-labelledby="risks-title">
        <h2 id="risks-title">Risks we noticed</h2>
        {report.risks.length === 0 ? (
          <p className="muted">None in your answers. Keep it that way.</p>
        ) : (
          <ul>{report.risks.map((flag) => <li key={flag}>{riskText(RISK_FOR_YOU, flag)}</li>)}</ul>
        )}
      </section>

      <section className="card" aria-labelledby="steps-title">
        <h2 id="steps-title">Next steps for your role</h2>
        <ul>{report.next_steps.map((step) => <li key={step}>{step}</li>)}</ul>
        <button type="button" className="secondary" onClick={onRetake}>Retake the diagnostic</button>
      </section>

      <section className="card" aria-labelledby="data-title">
        <h2 id="data-title">Your data</h2>
        <p>
          We store each answer you gave, its score, and for written answers the reason and any risks the AI noted.
          Leadership never sees your answers: the dashboard only shows teams of at least 5 people.
        </p>
        <DeleteMyData onDeleted={onDeleted} />
      </section>
    </>
  );
}

function Deleted({ result }) {
  return (
    <div className="success-box" role="status">
      <p><strong>Your answers have been deleted.</strong> Dashboards update immediately.</p>
      <ul>
        {Object.entries(result.deleted_answers).map(([org, count]) => (
          <li key={org}>{org}: {count} {count === 1 ? "answer" : "answers"} deleted</li>
        ))}
      </ul>
    </div>
  );
}
