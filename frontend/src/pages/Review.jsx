import React, { useState } from "react";
import { CircleCheck, TriangleAlert } from "lucide-react";
import { api } from "../api.js";
import { useApi } from "../useApi.js";
import { RISK_FOR_TEAMS, RUBRIC, reviewReason, riskText } from "../labels.js";
import { ErrorBox, Loading } from "../components/Status.jsx";
import Badge from "../components/Badge.jsx";

const SCORES = [1, 2, 3, 4, 5];

// The human review queue. The backend never sends who wrote an answer, and this page only
// shows the fields listed in ReviewItem, so nothing identifying can appear here.
export default function Review() {
  const { data, error, loading } = useApi("/review/queue");
  const [saved, setSaved] = useState([]); // review ids saved during this visit

  if (loading) return <Loading what="Loading the review queue" />;
  if (error) return <ErrorBox message={error} />;

  const waiting = data.filter((item) => !saved.includes(item.review_id));
  return (
    <div className="stack">
      <header className="greeting">
        <p className="muted">Answers the AI couldn't score. You won't see who wrote them.</p>
        <h1>Review</h1>
      </header>

      {saved.length > 0 && (
        <div className="box box-success" role="status">
          <CircleCheck size={18} aria-hidden="true" />
          <span>Review saved. The answer now counts in its writer's report and on the dashboard.</span>
        </div>
      )}

      {waiting.length === 0 ? (
        <section className="card empty" aria-labelledby="empty-review-title">
          <span className="icon-chip icon-chip-large" aria-hidden="true"><CircleCheck size={24} /></span>
          <h2 id="empty-review-title">Nothing to review</h2>
          <p className="muted">Answers the AI can't score will appear here.</p>
        </section>
      ) : (
        waiting.map((item) => (
          <ReviewItem key={item.review_id} item={item}
                      onSaved={() => setSaved((current) => [...current, item.review_id])} />
        ))
      )}
    </div>
  );
}

function ReviewItem({ item, onSaved }) {
  const [score, setScore] = useState(null);
  const [flags, setFlags] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const id = `review-${item.review_id}`;

  function toggleFlag(flag) {
    setFlags((current) => (current.includes(flag) ? current.filter((f) => f !== flag) : [...current, flag]));
  }

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/review/${item.review_id}`, { method: "POST", body: JSON.stringify({ score, flags }) });
      onSaved();
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <section className="card" aria-labelledby={`${id}-question`}>
      <form className="review-form" onSubmit={save}>
        <div className="review-head">
          {item.possible_injection && (
            <Badge tone="warn"><TriangleAlert size={14} aria-hidden="true" /> Possible prompt injection</Badge>
          )}
          <h2 id={`${id}-question`}>{item.question}</h2>
        </div>

        <blockquote className="review-answer">{item.answer}</blockquote>

        <div className="review-ai">
          <p><strong>Why it's here:</strong> {reviewReason(item.reason)}</p>
          {item.flags.length > 0 && (
            <p><strong>The AI flagged:</strong> {item.flags.map((f) => riskText(RISK_FOR_TEAMS, f)).join("; ")}</p>
          )}
          {item.adjustments.length > 0 && <p className="muted">AI notes: {item.adjustments.join("; ")}</p>}
        </div>

        <fieldset>
          <legend>Your score</legend>
          <div className="score-pills">
            {SCORES.map((n) => (
              <label key={n} className={score === n ? "choice score-pill is-checked" : "choice score-pill"}>
                <input type="radio" name={`${id}-score`} value={n} checked={score === n} onChange={() => setScore(n)} />
                <span className="score-pill-number">{n}</span>{" "}
                <span className="score-pill-text">{RUBRIC[n]}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>Risks in this answer</legend>
          <p className="muted small">Tick only what the answer shows. A data-sharing risk caps the score at 3.</p>
          <div className="choices">
            {Object.keys(RISK_FOR_TEAMS).map((flag) => (
              <label key={flag} className={flags.includes(flag) ? "choice is-checked" : "choice"}>
                <input type="checkbox" checked={flags.includes(flag)} onChange={() => toggleFlag(flag)} />
                <span>{riskText(RISK_FOR_TEAMS, flag)}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <ErrorBox message={error} />
        <button type="submit" disabled={score === null || busy}>{busy ? "Saving…" : "Save review"}</button>
      </form>
    </section>
  );
}
