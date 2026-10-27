from app.auth import DUMMY_PASSWORD_HASH, hash_password, verify_password
from app.config import BCRYPT_ROUNDS
from app.routes import auth_routes


def test_hash_is_not_the_plain_password():
    hashed = hash_password("pulse123")
    assert hashed != "pulse123"
    assert hashed.startswith("$2")  # bcrypt format


def test_same_password_hashes_differently_each_time():
    assert hash_password("pulse123") != hash_password("pulse123")


def test_verify_accepts_right_and_rejects_wrong_password():
    hashed = hash_password("pulse123")
    assert verify_password("pulse123", hashed)
    assert not verify_password("wrong", hashed)


def test_verify_rejects_old_sha256_hashes_instead_of_crashing():
    old_sha256_of_pulse123 = "c1e3bb1bbd0f5e0b6eb6ad2b9b7e1ea8d4ec1d1b0f7c2b23a9b3b0b4bdbe1a2f"
    assert not verify_password("pulse123", old_sha256_of_pulse123)


def test_login_fails_the_same_way_for_wrong_password_and_unknown_email(client):
    wrong_password = client.post("/auth/login", json={"email": "asha@northwind.test", "password": "wrong"})
    unknown_email = client.post("/auth/login", json={"email": "nobody@northwind.test", "password": "pulse123"})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_unknown_email_still_runs_a_password_check(client, monkeypatch):
    # Skipping bcrypt for unknown emails would make them answer faster and reveal who is registered.
    checked = []

    def spy(password, hashed):
        checked.append(hashed)
        return verify_password(password, hashed)

    monkeypatch.setattr(auth_routes, "verify_password", spy)
    r = client.post("/auth/login", json={"email": "nobody@northwind.test", "password": "pulse123"})
    assert r.status_code == 401
    assert checked == [DUMMY_PASSWORD_HASH]


def test_tests_use_cheap_bcrypt_rounds():
    assert BCRYPT_ROUNDS == 4
    assert hash_password("pulse123").startswith("$2b$04$")
