from datetime import datetime, timedelta, timezone

import jwt

from app.config import SECRET_KEY
from tests.conftest import login

NORTHWIND_ID = 1
BLUEPEAK_ID = 2


def test_login_lists_organizations(client):
    _, data = login(client, "ravi@consult.test")
    names = {o["org_name"] for o in data["organizations"]}
    assert names == {"Northwind Logistics", "Bluepeak Retail"}


def test_employee_sees_questions(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    r = client.get("/diagnostic/questions", headers=headers)
    assert r.status_code == 200
    assert any(q["id"] == "sup-drafts" for q in r.json())


def test_admin_dashboard(client):
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")
    r = client.get("/dashboard", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["departments"]) == 4


def test_admin_cannot_read_another_org_through_the_url(client):
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")
    r = client.get(f"/dashboard?org_id={BLUEPEAK_ID}", headers=headers)
    assert r.status_code == 200
    assert r.json()["organization"] == "Northwind Logistics"
    assert "Stores" not in {d["department"] for d in r.json()["departments"]}


def test_multi_org_admin_sees_only_the_org_in_the_token(client):
    headers, _ = login(client, "ravi@consult.test", "Bluepeak Retail")
    r = client.get(f"/dashboard?org_id={NORTHWIND_ID}", headers=headers)
    assert r.status_code == 200
    assert r.json()["organization"] == "Bluepeak Retail"
    assert {d["department"] for d in r.json()["departments"]} == {"Stores", "Customer Care"}


def test_multi_org_user_is_employee_in_other_org(client):
    headers, _ = login(client, "ravi@consult.test", "Northwind Logistics")
    assert client.get("/dashboard", headers=headers).status_code == 403


def test_select_org_rejects_orgs_the_user_is_not_in(client):
    headers, _ = login(client, "priya@northwind.test")
    for org_id in (BLUEPEAK_ID, 999):
        r = client.post("/auth/select-org", json={"org_id": org_id}, headers=headers)
        assert r.status_code == 403
        assert r.json()["detail"] == "Not a member of this organization"


def test_employee_cannot_see_dashboard(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    assert client.get("/dashboard", headers=headers).status_code == 403


def test_missing_garbage_and_expired_tokens_are_rejected(client):
    expired = jwt.encode(
        {"sub": "1", "org": NORTHWIND_ID, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        SECRET_KEY, algorithm="HS256",
    )
    for headers in ({}, {"Authorization": "Bearer not-a-token"}, {"Authorization": f"Bearer {expired}"}):
        assert client.get("/dashboard", headers=headers).status_code == 401


def test_token_without_selected_org_is_rejected(client):
    headers, _ = login(client, "asha@northwind.test")
    assert client.get("/dashboard", headers=headers).status_code == 400
    assert client.get("/reports/me", headers=headers).status_code == 400
