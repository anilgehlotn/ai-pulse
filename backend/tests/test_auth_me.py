"""GET /auth/me: who is signed in, their organizations, and the one selected in the token.

The frontend calls it on page load so a refresh restores the session instead of logging out.
"""
from tests.conftest import login


def test_me_without_an_organization_selected(client):
    headers, _ = login(client, "ravi@consult.test")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json() == {
        "name": "Ravi Kapoor",
        "email": "ravi@consult.test",
        "organizations": [
            {"org_id": 1, "org_name": "Northwind Logistics", "role": "employee"},
            {"org_id": 2, "org_name": "Bluepeak Retail", "role": "admin"},
        ],
        "selected_org": None,
    }


def test_me_with_an_organization_selected(client):
    headers, _ = login(client, "ravi@consult.test", "Bluepeak Retail")
    selected = client.get("/auth/me", headers=headers).json()["selected_org"]
    assert selected == {"org_id": 2, "org_name": "Bluepeak Retail", "role": "admin"}


def test_me_without_a_token_is_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_with_a_bad_token_is_401(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer not-a-token"}).status_code == 401
