import React, { useState } from "react";
import { api } from "../api.js";
import { useApi } from "../useApi.js";
import { ErrorBox, InfoBox, Loading } from "../components/Status.jsx";

const MAX_LENGTH = 2000; // same limit as MAX_ANSWER_LENGTH in the backend

export default function Diagnostic({ onSubmitted }) {
  const questions = useApi("/diagnostic/questions");
  const report = useApi("/reports/me");
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (questions.loading || report.loading) return <Loading what="Loading your questions" />;
  if (questions.error) return <ErrorBox message={questions.error} />;

  const list = questions.data;
  const isAnswered = (q) => (answers[q.id] || "").trim() !== "";
  const answeredCount = list.filter(isAnswered).length;
  const complete = answeredCount === list.length;
  const alreadySubmitted = report.data && report.data.answered > 0;

  function setAnswer(id, value) {
    setAnswers((current) => ({ ...current, [id]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload = list.map((q) => ({ question_id: q.id, answer: answers[q.id] }));
      await api("/diagnostic/submit", { method: "POST", body: JSON.stringify({ answers: payload }) });
      onSubmitted();
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  const common = list.filter((q) => q.roles.includes("all"));
  const forRole = list.filter((q) => !q.roles.includes("all"));

  return (
    <form className="stack" onSubmit={submit}>
      <header className="page-head">
        <h1>My diagnostic</h1>
        <p className="muted">There are no right answers. Pick what you actually do today.</p>
      </header>

      {alreadySubmitted && <InfoBox>Submitting again replaces your previous answers.</InfoBox>}

      <QuestionGroup title="About you and AI" questions={common} answers={answers} onChange={setAnswer} />
      {forRole.length > 0 && (
        <QuestionGroup title="Your role" questions={forRole} answers={answers} onChange={setAnswer} />
      )}

      <div className="submit-bar">
        <p className="progress" aria-live="polite">{answeredCount} of {list.length} answered</p>
        <ErrorBox message={error} />
        <button type="submit" disabled={!complete || submitting}>
          {submitting ? "Submitting…" : "Submit answers"}
        </button>
      </div>
    </form>
  );
}

function QuestionGroup({ title, questions, answers, onChange }) {
  return (
    <section className="stack" aria-label={title}>
      <h2>{title}</h2>
      {questions.map((q) => (q.type === "mcq"
        ? <ChoiceQuestion key={q.id} question={q} value={answers[q.id]} onChange={onChange} />
        : <OpenQuestion key={q.id} question={q} value={answers[q.id] || ""} onChange={onChange} />))}
    </section>
  );
}

function ChoiceQuestion({ question, value, onChange }) {
  return (
    <fieldset className="card question">
      <legend>{question.text}</legend>
      {question.options.map((option) => (
        <label key={option} className="choice">
          <input
            type="radio"
            name={question.id}
            value={option}
            checked={value === option}
            onChange={() => onChange(question.id, option)}
          />
          <span>{option}</span>
        </label>
      ))}
    </fieldset>
  );
}

function OpenQuestion({ question, value, onChange }) {
  const id = `answer-${question.id}`;
  return (
    <div className="card question">
      <label htmlFor={id} className="question-text">{question.text}</label>
      <textarea
        id={id}
        rows={5}
        maxLength={MAX_LENGTH}
        value={value}
        aria-describedby={`${id}-count ${id}-note`}
        onChange={(e) => onChange(question.id, e.target.value)}
      />
      <p id={`${id}-count`} className="muted small counter">{value.length} / {MAX_LENGTH} characters</p>
      <p id={`${id}-note`} className="note small">
        This answer is scored by AI. Emails and phone numbers are removed before it is sent (please leave
        out people's names too), and a person reviews anything the AI isn't sure about.
      </p>
    </div>
  );
}
