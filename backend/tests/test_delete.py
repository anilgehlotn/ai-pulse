"""DELETE /me/data: an employee deletes all their answers, everywhere, immediately."""
from app import models
from app.db import SessionLocal
from app.main import app
from tests.conftest import login
from tests.test_dashboard import northwind
from tests.test_privacy import subtraction_attack

CONFIRM = {"confirm": "DELETE"}


def delete_my_data(client, headers, body=CONFIRM):
    return client.request("DELETE", "/me/data", json=body, headers=headers)


def answer_count(email, org_name=None):
    db = SessionLocal()
    q = db.query(models.Response).join(models.Membership).join(models.User).filter(models.User.email == email)
    if org_name:
        q = q.join(models.Organization).filter(models.Organization.name == org_name)
    count = q.count()
    db.close()
    return count


def total_answers():
    db = SessionLocal()
    count = db.query(models.Response).count()
    db.close()
    return count


def deletion_events():
    db = SessionLocal()
    events = db.query(models.DeletionEvent).all()
    db.close()
    return events


def test_employee_deletes_all_their_answers(client):
    headers, _ = login(client, "priya@northwind.test")  # no organization selected
    r = delete_my_data(client, headers)
    assert r.status_code == 200
    assert r.json() == {"deleted_answers": {"Northwind Logistics": 2}, "total": 2}
    assert answer_count("priya@northwind.test") == 0


def test_works_with_an_org_scoped_token_too(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    assert delete_my_data(client, headers).status_code == 200


def test_report_is_empty_but_account_and_membership_remain(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    delete_my_data(client, headers)

    report = client.get("/reports/me", headers=headers).json()
    assert (report["answered"], report["average_score"], report["level"]) == (0, None, "Not assessed")
    assert report["risks"] == []
    # Still able to log in, pick the organization and take the diagnostic again.
    headers, data = login(client, "priya@northwind.test", "Northwind Logistics")
    assert [o["org_name"] for o in data["organizations"]] == ["Northwind Logistics"]
    assert client.get("/diagnostic/questions", headers=headers).status_code == 200


def test_deletion_shows_on_the_dashboard_immediately(client):
    before = northwind(client)
    assert before["groups"][0] == {"name": "Sales", "privacy": "shown", "employees": 6, "respondents": 5,
                                   "average_score": 2.78, "level": "Exploring",
                                   "adoption": 3.2, "safety": 2.2, "quadrant": "Exposed"}

    headers, _ = login(client, "neha@northwind.test")
    delete_my_data(client, headers)
    after = northwind(client)

    # Sales drops to 4 respondents, so it is merged into Other teams (4 + 3 + 3 = 10 respondents).
    assert [g["name"] for g in after["groups"]] == ["Support", "Other teams"]
    other = after["groups"][1]
    assert other["privacy"] == "merged"
    assert other["teams"] == ["Sales", "Engineering", "HR", "Unassigned"]
    assert other["respondents"] == 10
    # Rule d: nobody is hidden, so the overall figure stays, and nobody is left over by subtraction.
    assert after["overall"]["privacy"] == "shown"
    assert after["overall"]["respondents"] == 16
    assert subtraction_attack(after)[0] == 0


def test_deletion_that_leaves_a_hidden_group_hides_the_overall_figure(client):
    for email in ("imran@northwind.test", "ravi@consult.test"):
        headers, _ = login(client, email)
        delete_my_data(client, headers)
    data = northwind(client)
    assert data["groups"][-1]["privacy"] == "hidden"  # Engineering's 3 alone
    assert data["overall"]["privacy"] == "hidden"


def test_deleted_persons_flags_leave_the_risks(client):
    def unreviewed(data):
        return next(r["people"] for r in data["overall"]["top_risks"] if r["risk"] == "unreviewed_output")

    assert unreviewed(northwind(client)) == 5
    headers, _ = login(client, "neha@northwind.test")  # one of the five
    delete_my_data(client, headers)
    assert unreviewed(northwind(client)) == "fewer than 5"


def test_multi_org_user_is_deleted_from_every_org(client):
    northwind_count = answer_count("ravi@consult.test", "Northwind Logistics")
    bluepeak_count = answer_count("ravi@consult.test", "Bluepeak Retail")
    assert northwind_count > 0 and bluepeak_count > 0

    headers, _ = login(client, "ravi@consult.test")
    r = delete_my_data(client, headers)
    assert r.json() == {
        "deleted_answers": {"Northwind Logistics": northwind_count, "Bluepeak Retail": bluepeak_count},
        "total": northwind_count + bluepeak_count,
    }
    assert answer_count("ravi@consult.test") == 0


def test_deleting_never_touches_other_users(client):
    before_total = total_answers()
    vikram_before = answer_count("vikram@northwind.test")
    priya_before = answer_count("priya@northwind.test")

    headers, _ = login(client, "priya@northwind.test")
    delete_my_data(client, headers)

    assert answer_count("vikram@northwind.test") == vikram_before
    assert total_answers() == before_total - priya_before


def test_unauthenticated_request_is_rejected(client):
    before = total_answers()
    assert client.request("DELETE", "/me/data", json=CONFIRM).status_code == 401
    assert delete_my_data(client, {"Authorization": "Bearer not-a-token"}).status_code == 401
    assert total_answers() == before


def test_wrong_or_missing_confirmation_deletes_nothing(client):
    headers, _ = login(client, "priya@northwind.test")
    before = total_answers()
    for body in ({"confirm": "delete"}, {"confirm": "yes"}, {}, None):
        r = delete_my_data(client, headers, body)
        assert r.status_code == 400, body
    assert total_answers() == before
    assert deletion_events() == []


def test_deletion_is_logged_without_identifying_anyone(client):
    headers, _ = login(client, "priya@northwind.test")
    delete_my_data(client, headers)
    [event] = deletion_events()
    assert event.answers_deleted == 2
    assert event.deleted_at is not None
    assert set(models.DeletionEvent.__table__.columns.keys()) == {"id", "deleted_at", "answers_deleted"}


def test_deletion_log_is_not_readable_through_the_api(client):
    paths = {route.path for route in app.routes}
    assert not any("deletion" in p for p in paths)
    assert {p for p in paths if p.startswith("/me")} == {"/me/data"}
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")
    assert client.get("/me/data", headers=headers).status_code == 405
