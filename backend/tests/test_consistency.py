"""An open answer that scores far above the same person's MCQ answers is not trusted.

Only the model's raw reply is faked, so the real parser and data-risk cap run before the check.
Priya (support, junior) answers 5 MCQs and 1 open question; every MCQ option list runs 1 to 5 points.
"""
from app import models
from app.db import SessionLocal
from app.services import llm, scoring
from app.services.scoring import ScoreResult, check_against_mcq
from tests.conftest import login

PRIYA = ("priya@northwind.test", "Northwind Logistics")


def submit_with(client, monkeypatch, mcq_points, model_reply):
    """Submit Priya's diagnostic with every MCQ worth mcq_points and the model replying model_reply."""
    monkeypatch.setattr(llm, "score_answer", lambda question, answer: model_reply)
    headers, _ = login(client, *PRIYA)
    questions = client.get("/diagnostic/questions", headers=headers).json()
    answers = [
        {"question_id": q["id"], "answer": q["options"][mcq_points - 1] if q["type"] == "mcq" else "I use AI at work."}
        for q in questions
    ]
    r = client.post("/diagnostic/submit", json={"answers": answers}, headers=headers)
    return r, headers


def reply(score, flags=()):
    return '{"score": %d, "reason": "Model reason.", "flags": %s}' % (score, str(list(flags)).replace("'", '"'))


def priya_rows():
    db = SessionLocal()
    rows = (db.query(models.Response).join(models.Membership).join(models.User)
            .filter(models.User.email == PRIYA[0]).all())
    db.close()
    return rows


def open_row():
    return next(r for r in priya_rows() if r.question_id == "common-open")


def test_open_score_far_above_mcq_goes_to_review(client, monkeypatch):
    r, headers = submit_with(client, monkeypatch, mcq_points=2, model_reply=reply(5))
    assert r.status_code == 200

    row = open_row()
    assert (row.status, row.score, row.reason) == ("needs_review", None, "inconsistent_with_mcq")
    assert row.adjustments == ["inconsistent_with_mcq (model score 5, MCQ average 2.00)"]
    assert row.scoring_version == "open-v4"

    report = client.get("/reports/me", headers=headers).json()
    assert report["average_score"] == 2.0  # MCQs only; the open answer is excluded
    assert report["awaiting_review"] == 1


def test_gap_of_one_is_kept(client, monkeypatch):
    submit_with(client, monkeypatch, mcq_points=2, model_reply=reply(3))
    row = open_row()
    assert (row.status, row.score, row.adjustments) == ("scored", 3, [])


def test_gap_of_exactly_two_goes_to_review(client, monkeypatch):
    submit_with(client, monkeypatch, mcq_points=3, model_reply=reply(5))
    assert open_row().reason == "inconsistent_with_mcq"


def test_low_open_score_never_triggers(client, monkeypatch):
    submit_with(client, monkeypatch, mcq_points=4, model_reply=reply(1))
    row = open_row()
    assert (row.status, row.score) == ("scored", 1)


def test_check_runs_after_the_data_risk_cap(client, monkeypatch):
    # Model says 5 with a data flag -> cap makes it 3 -> still 2 above an MCQ average of 1.0.
    submit_with(client, monkeypatch, mcq_points=1, model_reply=reply(5, ["customer_data_shared"]))
    row = open_row()
    assert (row.status, row.reason) == ("needs_review", "inconsistent_with_mcq")
    assert row.adjustments == ["capped_for_data_risk", "inconsistent_with_mcq (model score 3, MCQ average 1.00)"]


def test_submission_succeeds_and_mcqs_are_saved(client, monkeypatch):
    r, _ = submit_with(client, monkeypatch, mcq_points=2, model_reply=reply(5))
    assert r.status_code == 200
    mcq_rows = [row for row in priya_rows() if row.status == "mcq"]
    assert len(mcq_rows) == 5
    assert all(row.score == 2 for row in mcq_rows)


# ---------- the helper on its own ----------

def scored(score):
    return ScoreResult(status="scored", score=score, reason="r", flags=["unreviewed_output"])


def test_no_mcq_answers_skips_the_check():
    assert check_against_mcq(scored(5), None) == scored(5)


def test_answers_already_needing_review_are_left_alone():
    result = ScoreResult(status="needs_review", reason="invalid_json")
    assert check_against_mcq(result, 1.0) == result


def test_threshold_uses_the_constant():
    assert scoring.INCONSISTENCY_GAP == 2
    assert check_against_mcq(scored(4), 2.01).status == "scored"     # gap 1.99
    assert check_against_mcq(scored(4), 2.0).status == "needs_review"  # gap 2.0


def test_flags_are_kept_for_the_reviewer():
    assert check_against_mcq(scored(5), 1.0).flags == ["unreviewed_output"]


def test_scoring_version_is_bumped():
    assert scoring.SCORING_VERSION == "open-v4"
