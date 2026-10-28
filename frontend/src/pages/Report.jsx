import React, { useState } from "react";
import { Award, Check, ClipboardList, Gauge, ShieldCheck, Sparkles, TriangleAlert } from "lucide-react";
import { useApi } from "../useApi.js";
import { RISK_FOR_YOU, hasValue, riskText, show } from "../labels.js";
import { ErrorBox, Loading } from "../components/Status.jsx";
import { QuadrantBadge } from "../components/Badge.jsx";
import Card from "../components/Card.jsx";
import StatTile from "../components/StatTile.jsx";
import RingGauge from "../components/RingGauge.jsx";
import ScoreBar from "../components/ScoreBar.jsx";
import DeleteMyData from "../components/DeleteMyData.jsx";

export default function Report({ firstName, onTakeDiagnostic }) {
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
      <header className="greeting">
        <p className="muted">{data.organization}</p>
        <h1>Your AI Pulse, {firstName}</h1>
      </header>

      {deleted && <Deleted result={deleted} />}

      {data.answered === 0 ? (
        <NotAssessed onTakeDiagnostic={onTakeDiagnostic} />
      ) : (
        <Results report={data} onRetake={onTakeDiagnostic} onDeleted={handleDeleted} />
      )}
    </div>
  );
}

function NotAssessed({ onTakeDiagnostic }) {
  return (
    <section className="card empty" aria-labelledby="empty-title">
      <span className="icon-chip icon-chip-large" aria-hidden="true"><ClipboardList size={24} /></span>
      <h2 id="empty-title">Not assessed</h2>
      <p className="muted">You haven't answered the diagnostic yet. It takes about five minutes.</p>
      <button type="button" onClick={onTakeDiagnostic}>Take the diagnostic</button>
    </section>
  );
}

// A 1-5 value with "/ 5" after it, or a dash and a note when the backend sent null.
function ScoreTile({ label, icon, value }) {
  return (
    <StatTile
      label={label}
      icon={icon}
      value={show(value)}
      suffix={hasValue(value) ? "/ 5" : undefined}
      visual={hasValue(value) ? <ScoreBar value={value} /> : <span className="stat-note">Not enough answers yet</span>}
    />
  );
}

function Results({ report, onRetake, onDeleted }) {
  const waiting = report.awaiting_review;
  return (
    <>
      <section aria-labelledby="level-title">
        <h2 id="level-title" className="visually-hidden">Your scores</h2>
        <div className="tiles">
          <StatTile label="Level" icon={Award} value={report.level} highlight />
          <ScoreTile label="Average score" icon={Gauge} value={report.average_score} />
          <ScoreTile label="Adoption" icon={Sparkles} value={report.adoption} />
          <ScoreTile label="Safety" icon={ShieldCheck} value={report.safety} />
        </div>
        {waiting > 0 && (
          <div className="box box-warn">
            {waiting === 1
              ? "1 answer is waiting for a human review and isn't counted yet."
              : `${waiting} answers are waiting for a human review and aren't counted yet.`}
          </div>
        )}
      </section>

      <div className="grid-3">
        <Card id="average" title="Your average">
          <RingGauge value={report.average_score} label="Your average score" />
          <p className="center muted">On a 1–5 scale</p>
        </Card>

        <Card id="quadrant" title="Where you stand">
          {report.quadrant && <p><QuadrantBadge quadrant={report.quadrant} /></p>}
          <p>{report.quadrant_explanation}</p>
          <p className="muted small">Adoption is how often and how deeply you use AI. Safety is reviewing output,
            protecting data and following the policy.</p>
        </Card>

        {report.focus_next && (
          <Card id="focus" title="Focus next" tone="accent">
            <p className="focus-tip">{report.focus_next.tip}</p>
          </Card>
        )}
      </div>

      <div className="grid-2">
        <Card id="risks" title="Risks we noticed">
          {report.risks.length === 0 ? (
            <p className="muted">None in your answers. Keep it that way.</p>
          ) : (
            <ul className="plain-list">
              {report.risks.map((flag) => (
                <li key={flag} className="icon-row">
                  <TriangleAlert size={18} className="warn-icon" aria-hidden="true" />
                  <span>{riskText(RISK_FOR_YOU, flag)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card id="steps" title="Next steps for your role">
          <ul className="plain-list checklist">
            {report.next_steps.map((step) => (
              <li key={step} className="icon-row">
                <span className="check" aria-hidden="true"><Check size={14} strokeWidth={3} /></span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
          <button type="button" className="secondary" onClick={onRetake}>Retake the diagnostic</button>
        </Card>
      </div>

      <Card id="data" title="Your data">
        <p>
          We store each answer you gave, its score, and for written answers the reason and any risks the AI noted.
          Leadership never sees your answers: the dashboard only shows teams of at least 5 people.
        </p>
        <DeleteMyData onDeleted={onDeleted} />
      </Card>
    </>
  );
}

function Deleted({ result }) {
  return (
    <div className="box box-success" role="status">
      <div>
        <p><strong>Your answers have been deleted.</strong> Dashboards update immediately.</p>
        <ul className="plain-list">
          {Object.entries(result.deleted_answers).map(([org, count]) => (
            <li key={org}>{org}: {count} {count === 1 ? "answer" : "answers"} deleted</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
