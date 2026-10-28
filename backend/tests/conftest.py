import os
import tempfile
import time

import pytest

# Must run before the app is imported: the engine is created from DATABASE_URL at import time.
# The directory and its database are deleted automatically when the test run ends.
_test_db_dir = tempfile.TemporaryDirectory(prefix="aipulse-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_test_db_dir.name, 'test.db')}"
os.environ["APP_ENV"] = "test"
os.environ["AI_MODE"] = "mock"
os.environ["BCRYPT_ROUNDS"] = "4"  # minimum cost: real hashing, fast tests
os.environ["LOGIN_MAX_FAILURES"] = "5"
os.environ["LOGIN_WINDOW_SECONDS"] = "900"
os.environ["LOGIN_MAX_PER_IP"] = "20"  # small, so the per-IP test is quick

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app import seed  # noqa: E402
from app.rate_limit import login_limiter  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_login_limiter():
    """Every test starts with no recorded login attempts and the real clock."""
    login_limiter.reset()
    login_limiter.clock = time.monotonic


@pytest.fixture()
def client():
    seed.run()
    return TestClient(app)


def login(client, email, org_name=None):
    r = client.post("/auth/login", json={"email": email, "password": "pulse123"})
    data = r.json()
    token = data["token"]
    if org_name:
        org = next(o for o in data["organizations"] if o["org_name"] == org_name)
        token = client.post("/auth/select-org", json={"org_id": org["org_id"]},
                            headers={"Authorization": f"Bearer {token}"}).json()["token"]
    return {"Authorization": f"Bearer {token}"}, data
