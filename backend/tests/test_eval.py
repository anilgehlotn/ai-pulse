from app import eval as harness
from app.services.scoring import ScoreResult

REQUIRED_FIELDS = {"id", "answer", "expected_score_range", "expected_flags", "forbidden_flags"}


def test_eval_set_is_well_formed():
    cases = harness.load_cases()
    assert 12 <= len(cases) <= 20
    assert len({c["id"] for c in cases}) == len(cases)
    assert sum(1 for c in cases if c.get("injection")) == 3
    for c in cases:
        assert REQUIRED_FIELDS <= set(c)
        low, high = c["expected_score_range"]
        assert 1 <= low <= high <= 5


def test_harness_runs_in_mock_mode_and_catches_every_injection(capsys):
    exit_code = harness.main()
    out = capsys.readouterr().out

    assert "mock mode" in out.lower()
    summary = harness.summarise(harness.run_cases(harness.load_cases()))
    assert summary["injections_caught"] == summary["injections_total"] == 3
    assert summary["parsed_ok_pct"] is not None
    # Mock mode gates only on injections: the canned replies are broken on purpose, so parsing can't be 100%.
    assert summary["parsed_ok_pct"] < 100
    assert exit_code == 0
    assert "only the injection gate applies" in out.lower()


def test_live_mode_gates_on_parsing_too(monkeypatch, capsys):
    monkeypatch.setattr(harness, "AI_MODE", "live")
    # Pretend the model returned garbage for everything: parsing fails, injections are still caught.
    monkeypatch.setattr(harness, "score_open_answer",
                        lambda question, answer: ScoreResult(status="needs_review", reason="possible_prompt_injection")
                        if "ignore" in answer.lower() or "you are now" in answer.lower()
                        else ScoreResult(status="needs_review", reason="invalid_json"))
    assert harness.main() == 1
    assert "FAIL" in capsys.readouterr().out


def test_summary_maths():
    rows = [
        {"case": {"expected_score_range": [3, 4], "expected_flags": ["policy_unaware"], "forbidden_flags": []},
         "result": ScoreResult(status="scored", score=4, reason="r", flags=["policy_unaware", "unreviewed_output"])},
        {"case": {"expected_score_range": [1, 2], "expected_flags": ["customer_data_shared"], "forbidden_flags": ["unreviewed_output"]},
         "result": ScoreResult(status="scored", score=3, reason="r", flags=["unreviewed_output"])},
        {"case": {"expected_score_range": [1, 5], "expected_flags": [], "forbidden_flags": []},
         "result": ScoreResult(status="needs_review", reason="invalid_json")},
        {"case": {"expected_score_range": [1, 1], "expected_flags": [], "forbidden_flags": [], "injection": True},
         "result": ScoreResult(status="needs_review", reason="possible_prompt_injection")},
    ]
    s = harness.summarise(rows)
    assert s["parsed_ok_pct"] == round(100 * 2 / 3, 1)      # 2 of 3 model-scored cases parsed
    assert s["in_range_pct"] == 50.0                         # 1 of the 2 scored cases in range
    assert s["flag_precision_pct"] == round(100 * 1 / 3, 1)  # 1 correct of 3 raised
    assert s["flag_recall_pct"] == 50.0                      # 1 found of 2 expected
    assert s["forbidden_flags_raised"] == 1
    assert (s["injections_caught"], s["injections_total"]) == (1, 1)
    assert s["needs_review"] == 2
