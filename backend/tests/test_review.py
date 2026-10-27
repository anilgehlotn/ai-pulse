"""Open answers the model can't score properly are saved as needs_review and kept out of the numbers."""
from app import models
from app.db import SessionLocal
from app.services import llm, scoring
from tests.conftest import login

PRIYA = ("priya@northwind.test", "Northwind Logistics")  # support, junior: 5 MCQs + common-open


def priya_answers(client, headers):
    questions = client.get("/diagnostic/questions", headers=headers).json()
    # Every MCQ gets its 4-point option.
    return [
        {"question_id": q["id"], "answer": q["options"][3] if q["type"] == "mcq" else "I summarise tickets with AI."}
        for q in questions
    ]


def stored_rows(question_id):
    """Priya's stored rows for one question."""
    db = SessionLocal()
    rows = (
        db.query(models.Response)
        .join(models.Membership).join(models.User)
        .filter(models.User.email == PRIYA[0], models.Response.question_id == question_id)
        .all()
    )
    db.close()
    return rows


def test_malformed_model_output_still_saves_the_submission(client, monkeypatch):
    monkeypatch.setattr(llm, "score_answer", lambda question, answer: "```json\n{not valid json\n```")
    headers, _ = login(client, *PRIYA)

    r = client.post("/diagnostic/submit", json={"answers": priya_answers(client, headers)}, headers=headers)
    assert r.status_code == 200

    [open_row] = stored_rows("common-open")
    assert open_row.status == "needs_review"
    assert open_row.score is None
    assert open_row.reason == "invalid_json"
    assert open_row.scoring_version == scoring.SCORING_VERSION

    [mcq_row] = [r for r in stored_rows("sup-drafts")]
    assert mcq_row.status == "mcq"
    assert mcq_row.score == 4
    assert mcq_row.scoring_version is None

    report = client.get("/reports/me", headers=headers).json()
    assert report["answered"] == 6
    assert report["awaiting_review"] == 1
    assert report["average_score"] == 4.0  # only the five MCQs, all 4 points


def test_scored_open_answer_is_stored_with_status_and_version(client, monkeypatch):
    monkeypatch.setattr(llm, "score_answer",
                        lambda question, answer: '{"score": 2, "reason": "Basic use.", "flags": ["policy_unaware"]}')
    headers, _ = login(client, *PRIYA)
    client.post("/diagnostic/submit", json={"answers": priya_answers(client, headers)}, headers=headers)

    [open_row] = stored_rows("common-open")
    assert (open_row.status, open_row.score, open_row.flags) == ("scored", 2, ["policy_unaware"])
    assert open_row.scoring_version == scoring.SCORING_VERSION

    report = client.get("/reports/me", headers=headers).json()
    assert report["awaiting_review"] == 0
    assert report["average_score"] == round((4 * 5 + 2) / 6, 2)
    assert report["risks"] == ["policy_unaware"]


def add_row(email, org_name, **fields):
    db = SessionLocal()
    m = (
        db.query(models.Membership)
        .join(models.User).join(models.Organization)
        .filter(models.User.email == email, models.Organization.name == org_name)
        .one()
    )
    db.add(models.Response(membership_id=m.id, question_id="common-open", answer="x", **fields))
    db.commit()
    db.close()


def test_needs_review_rows_are_excluded_from_report_averages_and_flags(client):
    # Even if a needs_review row somehow carried a score and flags, it must not count.
    add_row(*PRIYA, status="needs_review", score=5, flags=["unreviewed_output"], reason="invalid_json")
    headers, _ = login(client, *PRIYA)
    report = client.get("/reports/me", headers=headers).json()
    assert report["average_score"] == 2.5  # seeded 2 and 3 only
    assert report["risks"] == ["customer_data_shared"]
    assert report["awaiting_review"] == 1


def test_dashboard_counts_answers_awaiting_review_and_ignores_them(client):
    add_row(*PRIYA, status="needs_review", score=5, flags=["unreviewed_output"], reason="invalid_json")
    add_row("rohan@northwind.test", "Northwind Logistics", status="needs_review", reason="possible_prompt_injection")
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")
    data = client.get("/dashboard", headers=headers).json()

    assert data["awaiting_review"] == 2
    rows = {d["department"]: d for d in data["departments"]}
    assert rows["Support"]["average_score"] == 2.5
    assert rows["Sales"]["responded"] == 1  # Rohan only has an unscored answer
    assert data["top_risks"] == [["customer_data_shared", 1]]


def test_dashboard_review_count_is_per_org(client):
    add_row(*PRIYA, status="needs_review", reason="invalid_json")
    headers, _ = login(client, "meera@bluepeak.test", "Bluepeak Retail")
    assert client.get("/dashboard", headers=headers).json()["awaiting_review"] == 0
