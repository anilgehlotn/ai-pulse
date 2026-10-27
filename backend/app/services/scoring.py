import json
from typing import Literal

from pydantic import BaseModel

from . import llm
from .llm import ALLOWED_FLAGS

MAX_REASON_LENGTH = 300
# Stored with every open answer. Bump it whenever the prompt or the parsing rules change.
SCORING_VERSION = "open-v2"
# One try plus one retry.
MAX_ATTEMPTS = 2

# Cheap first line of defence: answers containing these are sent to a human, never to the model.
# Compared in lower case with whitespace collapsed.
INJECTION_PHRASES = (
    "ignore previous",
    "ignore all previous",
    "ignore the above",
    "ignore the rubric",
    "ignore your instructions",
    "system prompt",
    "you are now",
    "score 5",
    "score of 5",
    "give me a 5",
    "give me 5",
    "rate me 5",
    "employee_answer>",
)


class ScoreResult(BaseModel):
    """Outcome of scoring one open answer.

    status "scored": score is 1-5 and reason is the model's explanation.
    status "needs_review": score is None and reason is a short code saying why (e.g. "invalid_json").
    """
    status: Literal["scored", "needs_review"]
    score: int | None = None
    reason: str
    flags: list[str] = []
    dropped_unknown_flags: bool = False


def needs_review(reason: str) -> ScoreResult:
    return ScoreResult(status="needs_review", reason=reason)


def parse_model_output(raw: str) -> ScoreResult:
    """Turn the model's raw text into a ScoreResult. Never raises: bad output becomes needs_review."""
    # Models often wrap JSON in ```json fences or add a sentence around it,
    # so start at the first "{" and decode exactly one JSON value from there.
    start = (raw or "").find("{")
    if start == -1:
        return needs_review("invalid_json")
    try:
        data, _ = json.JSONDecoder().raw_decode(raw, start)
    except json.JSONDecodeError:
        return needs_review("invalid_json")

    score = data.get("score")
    # type() check on purpose: isinstance(True, int) is True in Python, and we must reject booleans.
    if type(score) is not int:
        return needs_review("invalid_score")
    if not 1 <= score <= 5:
        return needs_review("score_out_of_range")

    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return needs_review("missing_reason")

    flags = data.get("flags", [])
    if not isinstance(flags, list):
        return needs_review("invalid_flags")
    # dict.fromkeys removes duplicates and keeps the original order.
    kept = list(dict.fromkeys(f for f in flags if f in ALLOWED_FLAGS))

    return ScoreResult(
        status="scored",
        score=score,
        reason=reason.strip()[:MAX_REASON_LENGTH],
        flags=kept,
        dropped_unknown_flags=any(f not in ALLOWED_FLAGS for f in flags),
    )


def looks_like_injection(answer: str) -> bool:
    text = " ".join(answer.lower().split())
    return any(phrase in text for phrase in INJECTION_PHRASES)


def score_open_answer(question_text: str, answer: str) -> ScoreResult:
    """Score one open answer. Never raises: any failure comes back as needs_review with a reason."""
    if looks_like_injection(answer):
        return needs_review("possible_prompt_injection")

    for _ in range(MAX_ATTEMPTS):
        try:
            result = parse_model_output(llm.score_answer(question_text, answer))
        except llm.LLMError as error:
            result = needs_review(error.reason)
            if not error.retryable:
                return result
            continue
        if result.status == "scored":
            return result
    return result
