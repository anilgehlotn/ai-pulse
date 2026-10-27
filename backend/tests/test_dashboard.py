"""Expected values are worked out by hand from app/seed.py:

Northwind: Vikram (Sales) scored 4 and 4 -> 4.0. Priya (Support) scored 2 and 3 -> 2.5.
           Nobody in Engineering or HR answered. Asha is an admin with no department.
Bluepeak:  Tom (Stores) scored 3 -> 3.0. Kabir (Customer Care) scored 3 and 4 -> 3.5.
           Meera and Ravi are admins with no department.
"""
from app import models
from app.db import SessionLocal
from app.routes.dashboard import department_row
from app.utils import maturity_level
from tests.conftest import login


def dashboard(client, email, org_name):
    headers, _ = login(client, email, org_name)
    r = client.get("/dashboard", headers=headers)
    assert r.status_code == 200
    return r.json()


def rows_by_name(data):
    return {d["department"]: d for d in data["departments"]}


def add_response(email, org_name, question_id, score, flags):
    db = SessionLocal()
    m = (
        db.query(models.Membership)
        .join(models.User).join(models.Organization)
        .filter(models.User.email == email, models.Organization.name == org_name)
        .one()
    )
    db.add(models.Response(membership_id=m.id, question_id=question_id, answer="x", score=score, flags=flags))
    db.commit()
    db.close()


def test_northwind_department_averages(client):
    rows = rows_by_name(dashboard(client, "asha@northwind.test", "Northwind Logistics"))
    assert rows["Sales"] == {"department": "Sales", "employees": 3, "responded": 1,
                             "average_score": 4.0, "level": "Leader"}
    assert rows["Support"] == {"department": "Support", "employees": 3, "responded": 1,
                               "average_score": 2.5, "level": "Exploring"}


def test_bluepeak_department_averages_stay_on_the_1_to_5_scale(client):
    rows = rows_by_name(dashboard(client, "meera@bluepeak.test", "Bluepeak Retail"))
    assert rows["Stores"]["average_score"] == 3.0
    assert rows["Stores"]["level"] == "Practitioner"
    assert rows["Customer Care"]["average_score"] == 3.5
    assert rows["Customer Care"]["level"] == "Practitioner"


def test_department_average_is_mean_of_respondent_averages(client):
    # Neha answers 4 questions all scored 1 -> her average is 1.0.
    # Vikram is still 4.0, so Sales = (4.0 + 1.0) / 2 = 2.5, not (4+4+1+1+1+1) / 6 = 2.0.
    for qid in ("common-policy", "common-data", "common-review", "common-freq"):
        add_response("neha@northwind.test", "Northwind Logistics", qid, 1, [])
    sales = rows_by_name(dashboard(client, "asha@northwind.test", "Northwind Logistics"))["Sales"]
    assert sales["responded"] == 2
    assert sales["average_score"] == 2.5


def test_departments_without_respondents_are_not_assessed(client):
    rows = rows_by_name(dashboard(client, "asha@northwind.test", "Northwind Logistics"))
    for name in ("Engineering", "HR"):
        assert rows[name]["responded"] == 0
        assert rows[name]["average_score"] is None
        assert rows[name]["level"] == "Not assessed"


def test_members_without_department_are_grouped_as_unassigned(client):
    nw = rows_by_name(dashboard(client, "asha@northwind.test", "Northwind Logistics"))
    assert nw["Unassigned"]["employees"] == 1  # Asha
    bp = rows_by_name(dashboard(client, "meera@bluepeak.test", "Bluepeak Retail"))
    assert bp["Unassigned"]["employees"] == 2  # Meera and Ravi


def test_every_member_is_counted_exactly_once(client):
    data = dashboard(client, "asha@northwind.test", "Northwind Logistics")
    assert sum(d["employees"] for d in data["departments"]) == 11  # 10 Northwind people + Ravi


def test_risks_are_counted_per_person_not_per_answer(client):
    # Priya already has customer_data_shared on one answer; a second flagged answer must not double-count her.
    add_response("priya@northwind.test", "Northwind Logistics", "sup-drafts", 3, ["customer_data_shared"])
    data = dashboard(client, "asha@northwind.test", "Northwind Logistics")
    assert data["top_risks"] == [["customer_data_shared", 1]]

    # A second person with the flag does count.
    add_response("rohan@northwind.test", "Northwind Logistics", "common-open", 3, ["customer_data_shared"])
    data = dashboard(client, "asha@northwind.test", "Northwind Logistics")
    assert data["top_risks"] == [["customer_data_shared", 2]]


def test_department_row_with_no_respondents():
    assert department_row("HR", 2, []) == {
        "department": "HR", "employees": 2, "responded": 0, "average_score": None, "level": "Not assessed",
    }


def test_maturity_thresholds():
    assert maturity_level(None) == "Not assessed"
    assert maturity_level(1.99) == "Beginner"
    assert maturity_level(2.0) == "Exploring"
    assert maturity_level(3.0) == "Practitioner"
    assert maturity_level(4.0) == "Leader"


def test_report_and_dashboard_agree_on_level(client):
    # Priya averages 2.5 and is the only Support respondent, so both views must say the same level.
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    report = client.get("/reports/me", headers=headers).json()
    support = rows_by_name(dashboard(client, "asha@northwind.test", "Northwind Logistics"))["Support"]
    assert report["average_score"] == support["average_score"] == 2.5
    assert report["level"] == support["level"]


def test_tied_risks_are_listed_alphabetically(client):
    # Kabir has both flags once each; ties must not come out in random set order.
    data = dashboard(client, "meera@bluepeak.test", "Bluepeak Retail")
    assert data["top_risks"] == [["confidential_data_shared", 1], ["customer_data_shared", 1]]
