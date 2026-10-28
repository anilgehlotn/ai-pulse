"""Login rate limiting (issue #8): per email after failed attempts, and per client IP.

conftest.py resets the limiter before every test. Tests that need time to pass swap in a fake clock.
"""
import pytest

from app.config import LOGIN_MAX_FAILURES, LOGIN_MAX_PER_IP, LOGIN_WINDOW_SECONDS
from app.rate_limit import LoginLimiter, login_limiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture()
def clock():
    fake = FakeClock()
    login_limiter.clock = fake
    return fake


def attempt(client, email, password="wrong-password"):
    return client.post("/auth/login", json={"email": email, "password": password})


def fail(client, email, times=LOGIN_MAX_FAILURES):
    return [attempt(client, email).status_code for _ in range(times)]


def test_settings_used_by_these_tests():
    assert (LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS) == (5, 900)


def test_five_failures_lock_the_email_even_with_the_right_password(client):
    assert fail(client, "asha@northwind.test") == [401] * 5

    r = attempt(client, "asha@northwind.test", "pulse123")
    assert r.status_code == 429
    assert r.json()["detail"] == "Too many attempts. Try again in 15 minutes."
    assert r.headers["Retry-After"] == "900"


def test_lock_lifts_when_the_window_has_passed(client, clock):
    fail(client, "asha@northwind.test")

    clock.advance(LOGIN_WINDOW_SECONDS - 1)
    r = attempt(client, "asha@northwind.test", "pulse123")
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "1"
    assert r.json()["detail"] == "Too many attempts. Try again in 1 minute."

    clock.advance(1)
    assert attempt(client, "asha@northwind.test", "pulse123").status_code == 200


def test_refused_attempts_do_not_extend_the_lock(client, clock):
    fail(client, "asha@northwind.test")
    clock.advance(600)
    for _ in range(10):
        assert attempt(client, "asha@northwind.test").status_code == 429
    clock.advance(300)
    assert attempt(client, "asha@northwind.test", "pulse123").status_code == 200


def test_a_successful_login_clears_the_failures(client):
    fail(client, "asha@northwind.test", times=4)
    assert attempt(client, "asha@northwind.test", "pulse123").status_code == 200
    # The count starts again: four more failures are still only 401s, the fifth then locks.
    assert fail(client, "asha@northwind.test", times=5) == [401] * 5
    assert attempt(client, "asha@northwind.test", "pulse123").status_code == 429


def test_unknown_and_known_emails_are_limited_the_same_way(client):
    replies = {}
    for email in ["asha@northwind.test", "nobody@northwind.test"]:
        codes = fail(client, email)
        r = attempt(client, email)
        replies[email] = (codes, r.status_code, r.json(), r.headers["Retry-After"])
    assert replies["asha@northwind.test"] == replies["nobody@northwind.test"]


def test_the_email_is_compared_in_lower_case(client):
    fail(client, "Asha@Northwind.TEST")
    assert attempt(client, "asha@northwind.test", "pulse123").status_code == 429


def test_other_users_are_not_affected(client):
    fail(client, "asha@northwind.test")
    assert attempt(client, "rohan@northwind.test", "pulse123").status_code == 200


def test_too_many_attempts_from_one_ip_are_refused(client, clock):
    # Every attempt counts here, successful or not.
    for _ in range(LOGIN_MAX_PER_IP):
        assert attempt(client, "rohan@northwind.test", "pulse123").status_code == 200

    r = attempt(client, "asha@northwind.test", "pulse123")
    assert r.status_code == 429
    assert r.headers["Retry-After"] == "60"
    assert r.json()["detail"] == "Too many attempts. Try again in 1 minute."

    clock.advance(60)
    assert attempt(client, "asha@northwind.test", "pulse123").status_code == 200


def test_the_ip_limit_is_per_ip():
    clock = FakeClock()
    limiter = LoginLimiter(max_failures=5, window_seconds=900, max_per_ip=2, clock=clock)
    for _ in range(2):
        assert limiter.seconds_to_wait("a@x.test", "10.0.0.1") == 0
        limiter.record_attempt("10.0.0.1")
    assert limiter.seconds_to_wait("a@x.test", "10.0.0.1") == 60
    assert limiter.seconds_to_wait("a@x.test", "10.0.0.2") == 0


def test_the_limiter_counts_from_its_own_clock():
    clock = FakeClock()
    limiter = LoginLimiter(max_failures=2, window_seconds=100, max_per_ip=30, clock=clock)
    limiter.record_failure("a@x.test")
    clock.advance(30)
    limiter.record_failure("a@x.test")
    assert limiter.seconds_to_wait("a@x.test", "10.0.0.1") == 70  # until the first failure is 100s old
    clock.advance(70)
    assert limiter.seconds_to_wait("a@x.test", "10.0.0.1") == 0


def test_a_forwarded_for_header_does_not_change_the_ip(client):
    # X-Forwarded-For is set by the caller, so an attacker could rotate it to dodge the IP limit.
    for i in range(LOGIN_MAX_PER_IP):
        r = client.post("/auth/login", json={"email": "rohan@northwind.test", "password": "pulse123"},
                        headers={"X-Forwarded-For": f"10.0.0.{i}"})
        assert r.status_code == 200
    r = client.post("/auth/login", json={"email": "rohan@northwind.test", "password": "pulse123"},
                    headers={"X-Forwarded-For": "10.0.1.1"})
    assert r.status_code == 429
