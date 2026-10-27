import pytest

from app.services.profile import SAFETY_TIPS
from app.services.questions import load_questions, questions_for


def ids(qs):
    return {q["id"] for q in qs}


def test_everyone_gets_common_questions():
    got = ids(questions_for("sales", "junior"))
    assert {"common-freq", "common-policy", "common-data", "common-review", "common-open"} <= got


def test_junior_engineer_does_not_get_senior_questions():
    got = ids(questions_for("engineering", "junior"))
    assert "eng-assistant" in got
    assert "eng-review" not in got
    assert "eng-arch" not in got


def test_senior_support_gets_escalation_question():
    assert "sup-escalation" in ids(questions_for("support", "senior"))


def test_lead_manager_gets_policy_questions():
    got = ids(questions_for("manager", "lead"))
    assert "mgr-policy" in got
    assert "mgr-open" in got


def test_lead_engineer_gets_every_engineering_question():
    got = ids(questions_for("engineering", "lead"))
    assert {"eng-assistant", "eng-review", "eng-arch"} <= got


def test_mid_engineer_gets_review_but_not_architecture():
    got = ids(questions_for("engineering", "mid"))
    assert "eng-review" in got
    assert "eng-arch" not in got


def test_unknown_seniority_raises():
    with pytest.raises(ValueError, match="Unknown seniority 'principal'"):
        questions_for("engineering", "principal")


def test_every_mcq_is_tagged_adoption_or_safety():
    for q in load_questions():
        if q["type"] == "mcq":
            assert q.get("dimension") in ("adoption", "safety"), f"{q['id']} has dimension {q.get('dimension')!r}"
        else:
            assert "dimension" not in q, f"open question {q['id']} must not have a dimension"


def test_every_safety_question_has_a_tip():
    safety = {q["id"] for q in load_questions() if q.get("dimension") == "safety"}
    assert set(SAFETY_TIPS) == safety
