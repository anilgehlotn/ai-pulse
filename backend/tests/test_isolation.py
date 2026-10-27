import os
import tempfile

from app import config
from app.db import engine


def test_tests_run_with_app_env_test():
    assert config.APP_ENV == "test"


def test_tests_use_a_temporary_database():
    backend_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.realpath(engine.url.database)
    assert db_path.startswith(os.path.realpath(tempfile.gettempdir()))
    assert not db_path.startswith(backend_dir)
