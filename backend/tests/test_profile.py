"""Adoption vs safety for one person (app/services/profile.py) and on /reports/me.

Seeded people used below (app/seed.py):
  Rohan (sales, mid): adoption questions common-freq, sales-outreach, sales-crm all 3 points;
         safety questions common-policy, common-data, common-review all 2 points.
         -> adoption 3.0, safety 2.0, "Exposed". All three safety answers tie at 2, so the
            tie-break order picks common-data.
  Priya (support, junior): only common-freq (2) and an open answer -> adoption 2.0, no safety score.
"""
from types import SimpleNamespace

import pytest

from app.services.profile import (QUADRANT_THRESHOLD, SAFETY_TIPS, dimension_scores, quadrant,
                                  weakest_safety_habit)
from tests.conftest import login


def row(question_id, score, status="mcq"):
    return SimpleNamespace(question_id=question_id, score=score, status=status)


def report(client, email):
    headers, _ = login(client, email, "Northwind Logistics")
    return client.get("/reports/me", headers=headers).json()


# ---------- quadrant ----------

def test_threshold_is_3():
    assert QUADRANT_THRESHOLD == 3


@pytest.mark.parametrize("adoption, safety, expected", [
    (3, 3, "Leading"),            # exactly 3 counts as "high" on both axes
    (5, 4.5, "Leading"),
    (3, 2.99, "Exposed"),
    (4.2, 1, "Exposed"),
    (2.99, 3, "Cautious"),
    (1, 5, "Cautious"),
    (2.99, 2.99, "Getting started"),
])
def test_quadrant_boundaries(adoption, safety, expected):
    assert quadrant(adoption, safety) == expected


@pytest.mark.parametrize("adoption, safety", [(None, 4), (4, None), (None, None)])
def test_quadrant_needs_both_scores(adoption, safety):
    assert quadrant(adoption, safety) is None


# ---------- dimension scores ----------

def test_dimension_scores_average_each_dimension_separately():
    rows = [row("common-freq", 5), row("sales-outreach", 4),       # adoption: 4.5
            row("common-data", 1), row("common-review", 2),        # safety: 1.5
            row("common-open", 5, status="scored")]                # open: no dimension, ignored
    assert dimension_scores(rows) == {"adoption": 4.5, "safety": 1.5}


def test_missing_dimension_is_none():
    assert dimension_scores([row("common-freq", 4)]) == {"adoption": 4.0, "safety": None}
    assert dimension_scores([]) == {"adoption": None, "safety": None}


# ---------- weakest safety habit ----------

def test_weakest_habit_is_the_lowest_safety_answer():
    rows = [row("common-freq", 1),  # adoption: never the weakest *safety* habit
            row("common-policy", 4), row("common-review", 2), row("common-data", 3)]
    assert weakest_safety_habit(rows) == "common-review"


def test_weakest_habit_tie_is_broken_by_the_tip_order():
    # common-data comes before common-review and common-policy in SAFETY_TIPS.
    rows = [row("common-policy", 2), row("common-review", 2), row("common-data", 2)]
    assert list(SAFETY_TIPS)[0] == "common-data"
    assert weakest_safety_habit(rows) == "common-data"


def test_no_safety_answers_means_no_weakest_habit():
    assert weakest_safety_habit([row("common-freq", 2)]) is None


# ---------- /reports/me ----------

def test_report_for_an_exposed_seeded_user(client):
    data = report(client, "rohan@northwind.test")
    assert data["adoption"] == 3.0
    assert data["safety"] == 2.0
    assert data["quadrant"] == "Exposed"
    assert data["quadrant_explanation"].startswith("You use AI a lot")
    assert data["focus_next"] == {"question_id": "common-data", "tip": SAFETY_TIPS["common-data"]}
    # Existing fields are still there: 18 points over 7 answers.
    assert (data["answered"], data["average_score"], data["level"]) == (7, 2.57, "Exploring")


def test_report_without_safety_answers(client):
    data = report(client, "priya@northwind.test")
    assert (data["adoption"], data["safety"], data["quadrant"], data["focus_next"]) == (2.0, None, None, None)
    assert data["quadrant_explanation"]  # still one sentence telling her what to do
