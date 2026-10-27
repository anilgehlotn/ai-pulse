import pytest

from app import models
from app.db import SessionLocal
from app.routes import diagnostic
from tests.conftest import login

PRIYA = ("priya@northwind.test", "Northwind Logistics")  # support, junior; already has 2 seeded answers


@pytest.fixture(autouse=True)
def fixed_open_score(monkeypatch):
    """Score open answers with a fixed result so tests don't depend on the mock LLM."""
    monkeypatch.setattr(diagnostic, "score_open_answer",
                        lambda question, answer: {"score": 3, "reason": "ok", "flags": []})


def full_answers(client, headers, mcq_choice=0):
    """One valid answer for every question assigned to the logged-in member."""
    questions = client.get("/diagnostic/questions", headers=headers).json()
    return [
        {"question_id": q["id"], "answer": q["options"][mcq_choice] if q["type"] == "mcq" else "I drafted replies with AI."}
        for q in questions
    ]


def submit(client, headers, answers):
    return client.post("/diagnostic/submit", json={"answers": answers}, headers=headers)


def response_count(email, org_name):
    db = SessionLocal()
    count = (
        db.query(models.Response)
        .join(models.Membership).join(models.User).join(models.Organization)
        .filter(models.User.email == email, models.Organization.name == org_name)
        .count()
    )
    db.close()
    return count


def test_valid_submission_is_saved(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers)
    r = submit(client, headers, answers)
    assert r.status_code == 200
    assert r.json() == {"saved": 6}


def test_question_for_another_role_is_rejected(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers) + [{"question_id": "eng-assistant", "answer": "I don't"}]
    r = submit(client, headers, answers)
    assert r.status_code == 400
    assert "eng-assistant" in r.json()["detail"]


def test_duplicate_answer_is_rejected(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers)
    r = submit(client, headers, answers + [answers[0]])
    assert r.status_code == 400
    assert "Duplicate" in r.json()["detail"]
    assert answers[0]["question_id"] in r.json()["detail"]


def test_missing_answer_is_rejected(client):
    headers, _ = login(client, *PRIYA)
    answers = [a for a in full_answers(client, headers) if a["question_id"] != "sup-drafts"]
    r = submit(client, headers, answers)
    assert r.status_code == 400
    assert "Missing" in r.json()["detail"]
    assert "sup-drafts" in r.json()["detail"]


def test_wrong_mcq_option_is_rejected(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers)
    answers[0]["answer"] = "Sometimes, I guess"
    assert submit(client, headers, answers).status_code == 400


def test_blank_open_answer_is_rejected(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers)
    open_answer = next(a for a in answers if a["question_id"] == "common-open")
    open_answer["answer"] = "   \n "
    r = submit(client, headers, answers)
    assert r.status_code == 400
    assert "common-open" in r.json()["detail"]


def test_too_long_answer_is_rejected(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers)
    open_answer = next(a for a in answers if a["question_id"] == "common-open")
    open_answer["answer"] = "a" * 2001
    assert submit(client, headers, answers).status_code == 422


def test_open_answer_is_stored_stripped(client):
    headers, _ = login(client, *PRIYA)
    answers = full_answers(client, headers)
    next(a for a in answers if a["question_id"] == "common-open")["answer"] = "  Used AI daily.  "
    assert submit(client, headers, answers).status_code == 200
    db = SessionLocal()
    stored = db.query(models.Response).filter_by(question_id="common-open", answer="Used AI daily.").count()
    db.close()
    assert stored == 1


def test_rejected_submission_saves_nothing(client):
    headers, _ = login(client, *PRIYA)
    before = response_count(*PRIYA)
    answers = full_answers(client, headers)
    answers[-1]["answer"] = "not an option"  # valid answers first, the bad one last
    assert submit(client, headers, answers).status_code == 400
    assert response_count(*PRIYA) == before


def test_resubmitting_replaces_previous_answers(client):
    headers, _ = login(client, *PRIYA)
    assert response_count(*PRIYA) == 2  # seeded
    assert submit(client, headers, full_answers(client, headers)).status_code == 200
    assert response_count(*PRIYA) == 6
    assert submit(client, headers, full_answers(client, headers)).status_code == 200
    assert response_count(*PRIYA) == 6


def test_report_after_resubmit_reflects_only_latest_answers(client):
    headers, _ = login(client, *PRIYA)
    submit(client, headers, full_answers(client, headers, mcq_choice=4))  # MCQs score 5
    submit(client, headers, full_answers(client, headers, mcq_choice=0))  # MCQs score 1
    report = client.get("/reports/me", headers=headers).json()
    # Latest attempt only: five MCQs at 1 point and the open answer at 3 -> 8 / 6
    assert report["answered"] == 6
    assert report["average_score"] == round(8 / 6, 2)


def test_scoring_error_rolls_back_everything(client, monkeypatch):
    headers, _ = login(client, *PRIYA)
    before = response_count(*PRIYA)

    def broken_scorer(question, answer):
        raise RuntimeError("LLM is down")

    monkeypatch.setattr(diagnostic, "score_open_answer", broken_scorer)
    with pytest.raises(RuntimeError):
        submit(client, headers, full_answers(client, headers))
    assert response_count(*PRIYA) == before  # old answers kept, nothing new saved


def test_admin_can_take_the_diagnostic(client):
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")  # admin, manager, lead
    answers = full_answers(client, headers)
    assert {"mgr-policy", "mgr-open"} <= {a["question_id"] for a in answers}
    r = submit(client, headers, answers)
    assert r.status_code == 200
    assert response_count("asha@northwind.test", "Northwind Logistics") == len(answers)
