import json
import os

import pytest

from app.services.scoring import parse_model_output

_CANNED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mock_ai_responses.json")
with open(_CANNED_PATH) as f:
    CANNED = json.load(f)


def scored(score, reason, flags=(), dropped=False):
    return {"status": "scored", "score": score, "reason": reason, "flags": list(flags),
            "dropped_unknown_flags": dropped, "adjustments": []}


def needs_review(reason):
    return {"status": "needs_review", "score": None, "reason": reason, "flags": [],
            "dropped_unknown_flags": False, "adjustments": []}


# Expected outcome for each canned response in data/mock_ai_responses.json, in file order.
EXPECTED = [
    scored(4, "Uses AI weekly to draft and then checks replies before sending."),
    scored(3, "Regular use for summarising, little evidence of reviewing outputs.", ["unreviewed_output"]),
    scored(2, "Tried AI once for an email; no regular use."),
    scored(5, "Built a reusable prompt workflow the team now uses, with checks."),
    scored(3, "Uses AI for reports but pasted a customer list into a public tool.", ["customer_data_shared"]),
    needs_review("score_out_of_range"),   # score 7
    needs_review("missing_reason"),       # no reason
    needs_review("invalid_score"),        # score "four"
    scored(2, "Limited use.", dropped=True),  # made-up flags dropped
    scored(4, "Thoughtful use with review."),  # wrapped in ```json fences
]


def test_every_canned_response_has_an_expected_outcome():
    assert len(CANNED) == len(EXPECTED) == 10


@pytest.mark.parametrize("index", range(10))
def test_canned_response(index):
    assert parse_model_output(CANNED[index]).model_dump() == EXPECTED[index]


@pytest.mark.parametrize("bad_score", ["3.5", "true", "null", "0", "6", "-1", '"4"'])
def test_score_must_be_an_integer_from_1_to_5(bad_score):
    raw = '{"score": %s, "reason": "r", "flags": []}' % bad_score
    assert parse_model_output(raw).status == "needs_review"


def test_out_of_range_and_wrong_type_have_different_reasons():
    assert parse_model_output('{"score": 6, "reason": "r"}').reason == "score_out_of_range"
    assert parse_model_output('{"score": 3.5, "reason": "r"}').reason == "invalid_score"
    assert parse_model_output('{"score": true, "reason": "r"}').reason == "invalid_score"
    assert parse_model_output('{"reason": "r"}').reason == "invalid_score"


def test_text_around_the_json_is_ignored():
    raw = 'Sure! Here is the result:\n{"score": 3, "reason": "Fine.", "flags": []}\nHope that helps {really}.'
    assert parse_model_output(raw).model_dump() == scored(3, "Fine.")


def test_only_the_first_object_is_used():
    raw = '{"score": 2, "reason": "First."} {"score": 5, "reason": "Second."}'
    assert parse_model_output(raw).score == 2


@pytest.mark.parametrize("raw", ["", "not json at all", "{broken", "[1, 2, 3]", None])
def test_unparseable_output_is_invalid_json(raw):
    assert parse_model_output(raw).model_dump() == needs_review("invalid_json")


def test_blank_reason_is_rejected():
    assert parse_model_output('{"score": 3, "reason": "   "}').reason == "missing_reason"


def test_long_reason_is_trimmed_to_300_characters():
    raw = json.dumps({"score": 3, "reason": "  " + "x" * 500 + "  ", "flags": []})
    assert parse_model_output(raw).reason == "x" * 300


def test_flags_are_deduplicated_and_unknown_ones_dropped():
    raw = json.dumps({"score": 3, "reason": "r",
                      "flags": ["policy_unaware", "made_up", "policy_unaware", "customer_data_shared"]})
    result = parse_model_output(raw)
    assert result.flags == ["policy_unaware", "customer_data_shared"]
    assert result.dropped_unknown_flags is True


def test_flags_that_are_not_a_list_are_rejected():
    assert parse_model_output('{"score": 3, "reason": "r", "flags": "policy_unaware"}').reason == "invalid_flags"


def test_missing_flags_means_no_flags():
    assert parse_model_output('{"score": 3, "reason": "r"}').model_dump() == scored(3, "r")
