from app.models import utc_now


def test_timestamps_are_timezone_aware():
    assert utc_now().utcoffset().total_seconds() == 0
