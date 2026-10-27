"""python -m app.seed --if-empty: Docker runs it on every start, so it must never wipe existing data."""
from app import models, seed
from app.db import Base, SessionLocal, engine


def user_count():
    db = SessionLocal()
    count = db.query(models.User).count()
    db.close()
    return count


def test_if_empty_seeds_a_new_database():
    Base.metadata.drop_all(bind=engine)  # a brand-new volume has no tables at all
    assert seed.run_if_empty() is True
    assert user_count() > 0


def test_if_empty_leaves_existing_data_alone(client):
    db = SessionLocal()
    db.add(models.User(name="Real Person", email="real@client.test", password_hash="x"))
    db.commit()
    db.close()
    before = user_count()

    assert seed.run_if_empty() is False
    assert user_count() == before  # nothing dropped, nothing re-seeded


def test_command_line_flag(monkeypatch):
    calls = []
    monkeypatch.setattr(seed, "run_if_empty", lambda: calls.append("if_empty"))
    monkeypatch.setattr(seed, "run", lambda: calls.append("run"))
    seed.main(["--if-empty"])
    seed.main([])
    assert calls == ["if_empty", "run"]
