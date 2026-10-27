"""/dashboard on the demo seed. Expected values worked out by hand from app/seed.py.

Northwind respondents (each person's own average; adoption / safety in brackets):
  Sales:       Vikram (4 + 4 + 2) / 3 = 3.33 [4 / 2]
               Neha (2 + 2 + 1 + 1 + 1 + open 2) / 6 = 1.5 [2 / 1]
               Rohan (3 + 3 + 3 + 2 + 2 + 2 + open 3) / 7 = 2.57 [3 / 2]
               Anita 5 [5 / 5], Karan 1.5 [2 / 1] (same questions as Neha)
               -> 5 respondents, 13.90 / 5 = 2.78
               (Farah has not answered; 6 employees)
               adoption (4 + 2 + 3 + 5 + 2) / 5 = 3.2, safety (2 + 1 + 2 + 5 + 1) / 5 = 2.2 -> Exposed
  Support:     Priya 2.5, Arjun 4, Kavitha 3, Lakshmi 3, Nikhil 2, Tara 4 -> 6, 18.5 / 6 = 3.08
               adoption (Priya 2 + 4 + 3 + 3 + 2 + 4) / 6 = 3.0,
               safety (Priya has none: 4 + 3 + 3 + 2 + 4) / 5 = 3.2 -> Leading
  Engineering: Dev 4, Sara 3, Omar 2 -> 3      HR: Imran 2, Ravi 3 -> 2      Unassigned: Asha, no answers
  Other teams = Engineering + HR + Unassigned -> 5 respondents, (9 + 5) / 5 = 2.8, 6 employees
               adoption = safety = 2.8 (everyone answered both at their level) -> Getting started
  Overall: 16 respondents, (13.90 + 18.5 + 14) / 16 = 2.90
  act_first: Sales only, gap 3.2 - 2.2 = 1.0.
  unreviewed_output: Neha, Rohan, Karan, Nikhil, Omar = 5. customer_data_shared: Priya, Kavitha, Lakshmi = 3.
  policy_unaware: Imran = 1. confidential_data_shared: nobody in Northwind.
Bluepeak respondents: Tom (Stores), Kabir (Customer Care), Ravi (Unassigned) -> 3 in total, all hidden.
"""
from app import models
from app.db import SessionLocal
from tests.conftest import login
from tests.test_privacy import subtraction_attack

FEWER = "fewer than 5"


def dashboard(client, email, org_name):
    headers, _ = login(client, email, org_name)
    r = client.get("/dashboard", headers=headers)
    assert r.status_code == 200
    return r.json()


def northwind(client):
    return dashboard(client, "asha@northwind.test", "Northwind Logistics")


def remove_answers(email, org_name):
    db = SessionLocal()
    m = (
        db.query(models.Membership)
        .join(models.User).join(models.Organization)
        .filter(models.User.email == email, models.Organization.name == org_name)
        .one()
    )
    db.query(models.Response).filter_by(membership_id=m.id).delete()
    db.commit()
    db.close()


def test_northwind_dashboard(client):
    assert northwind(client) == {
        "organization": "Northwind Logistics",
        "min_group_size": 5,
        "groups": [
            {"name": "Sales", "privacy": "shown", "employees": 6, "respondents": 5,
             "average_score": 2.78, "level": "Exploring",
             "adoption": 3.2, "safety": 2.2, "quadrant": "Exposed"},
            {"name": "Support", "privacy": "shown", "employees": 6, "respondents": 6,
             "average_score": 3.08, "level": "Practitioner",
             "adoption": 3.0, "safety": 3.2, "quadrant": "Leading"},
            {"name": "Other teams", "privacy": "merged", "teams": ["Engineering", "HR", "Unassigned"],
             "employees": 6, "respondents": 5, "average_score": 2.8, "level": "Exploring",
             "adoption": 2.8, "safety": 2.8, "quadrant": "Getting started"},
        ],
        "act_first": [
            {"name": "Sales", "adoption": 3.2, "safety": 2.2, "gap": 1.0,
             "reason": "Uses AI often (3.2) but safety habits are low (2.2)"},
        ],
        "overall": {
            "privacy": "shown", "respondents": 16, "average_score": 2.9, "level": "Exploring",
            "top_risks": [
                {"risk": "unreviewed_output", "people": 5},
                {"risk": "confidential_data_shared", "people": FEWER},
                {"risk": "customer_data_shared", "people": FEWER},
                {"risk": "policy_unaware", "people": FEWER},
            ],
            "awaiting_review": FEWER,
        },
    }


def test_bluepeak_dashboard_hides_everything(client):
    data = dashboard(client, "ravi@consult.test", "Bluepeak Retail")
    assert data["groups"] == [{"name": "Other teams", "privacy": "hidden", "teams_hidden": 3,
                               "message": "3 teams hidden to protect anonymity"}]
    assert data["overall"]["privacy"] == "hidden"
    assert data["act_first"] == []
    assert subtraction_attack(data) is None


def test_respondent_means_at_least_one_saved_answer(client):
    # Farah (Sales) has no answers: she counts as an employee but not a respondent.
    sales = northwind(client)["groups"][0]
    assert (sales["employees"], sales["respondents"]) == (6, 5)


def test_hidden_remainder_hides_the_overall_figure(client):
    # Without HR's answers, Other teams is Engineering's 3 people: too small, so it and the overall go.
    remove_answers("imran@northwind.test", "Northwind Logistics")
    remove_answers("ravi@consult.test", "Northwind Logistics")
    data = northwind(client)
    assert [g["privacy"] for g in data["groups"]] == ["shown", "shown", "hidden"]
    assert data["overall"]["privacy"] == "hidden"
    assert subtraction_attack(data) is None


def test_attacker_finds_nobody_left_over_on_the_real_dashboard(client):
    left_over, _ = subtraction_attack(northwind(client))
    assert left_over == 0


def test_response_only_contains_published_fields(client):
    data = northwind(client)
    assert set(data) == {"organization", "min_group_size", "groups", "act_first", "overall"}
    for g in data["groups"]:
        assert set(g) <= {"name", "privacy", "teams", "teams_hidden", "message",
                          "employees", "respondents", "average_score", "level",
                          "adoption", "safety", "quadrant"}
    for row in data["act_first"]:
        assert set(row) == {"name", "adoption", "safety", "gap", "reason"}


QUADRANTS = {"Leading", "Exposed", "Cautious", "Getting started"}


def all_keys(value):
    """Every dictionary key anywhere in a JSON value."""
    if isinstance(value, dict):
        return set(value) | {k for v in value.values() for k in all_keys(v)}
    if isinstance(value, list):
        return {k for v in value for k in all_keys(v)}
    return set()


def test_no_counts_of_people_per_quadrant(client):
    # A quadrant only ever appears as a group's label, never as a key with a number of people.
    for data in (northwind(client), dashboard(client, "ravi@consult.test", "Bluepeak Retail")):
        keys = all_keys(data)
        assert not keys & QUADRANTS
        assert not {k for k in keys if "quadrant" in k.lower() and k != "quadrant"}


def test_seed_prints_a_summary(capsys):
    from app import seed
    seed.run()
    out = capsys.readouterr().out
    assert "Northwind Logistics: Sales 5, Support 6, Engineering 3, HR 2, Unassigned 0" in out
    assert "Bluepeak Retail: Stores 1, Customer Care 1, Unassigned 1" in out
