"""Measure the open-answer scoring pipeline against hand-written cases.

Run: python -m app.eval
Uses whatever AI_MODE is configured. Exits non-zero if any model output fails to parse
or any prompt injection gets through.
"""
import json
import os
import sys

from .config import AI_MODE
from .services.questions import load_questions
from .services.scoring import score_open_answer

_CASES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "eval_set.json")
QUESTION_ID = "common-open"


def load_cases():
    with open(_CASES_PATH) as f:
        return json.load(f)


def run_cases(cases):
    """Score every case through the real pipeline. Returns [{"case": ..., "result": ScoreResult}]."""
    question = next(q["text"] for q in load_questions() if q["id"] == QUESTION_ID)
    return [{"case": c, "result": score_open_answer(question, c["answer"])} for c in cases]


def pct(part, whole):
    return round(100 * part / whole, 1) if whole else None


def in_range(case, result):
    low, high = case["expected_score_range"]
    return result.status == "scored" and low <= result.score <= high


def summarise(rows):
    injections = [r for r in rows if r["case"].get("injection")]
    normal = [r for r in rows if not r["case"].get("injection")]
    scored = [r for r in normal if r["result"].status == "scored"]

    # Flag precision: of the flags raised, how many were expected. Recall: of the expected, how many were raised.
    raised = expected = correct = forbidden = 0
    for r in scored:
        got = set(r["result"].flags)
        raised += len(got)
        expected += len(r["case"]["expected_flags"])
        correct += len(got & set(r["case"]["expected_flags"]))
        forbidden += len(got & set(r["case"]["forbidden_flags"]))

    return {
        "cases": len(rows),
        "parsed_ok_pct": pct(len(scored), len(normal)),
        "in_range_pct": pct(sum(in_range(r["case"], r["result"]) for r in scored), len(scored)),
        "flag_precision_pct": pct(correct, raised),
        "flag_recall_pct": pct(correct, expected),
        "forbidden_flags_raised": forbidden,
        "injections_caught": sum(r["result"].reason == "possible_prompt_injection" for r in injections),
        "injections_total": len(injections),
        "false_injection_alarms": sum(r["result"].reason == "possible_prompt_injection" for r in normal),
        "needs_review": sum(r["result"].status == "needs_review" for r in rows),
    }


def print_table(rows):
    print(f"{'case':<28} {'status':<13} {'score':>5} {'expect':>6}  {'ok':<3} {'flags / reason'}")
    print("-" * 100)
    for r in rows:
        case, result = r["case"], r["result"]
        low, high = case["expected_score_range"]
        if case.get("injection"):
            ok = "yes" if result.reason == "possible_prompt_injection" else "NO"
        else:
            ok = "yes" if in_range(case, result) else "no"
        detail = (", ".join(result.flags) or "-") if result.status == "scored" else result.reason
        score = "-" if result.score is None else result.score
        print(f"{case['id']:<28} {result.status:<13} {score:>5} {f'{low}-{high}':>6}  {ok:<3} {detail}")


def show(value):
    return "n/a" if value is None else f"{value}%"


def main():
    rows = run_cases(load_cases())
    s = summarise(rows)

    print(f"AI_MODE={AI_MODE}\n")
    print_table(rows)
    print()
    totals = [
        ("Parsed OK", f"{show(s['parsed_ok_pct'])} of non-injection cases"),
        ("Score in expected range", f"{show(s['in_range_pct'])} of scored cases"),
        ("Flag precision", show(s["flag_precision_pct"])),
        ("Flag recall", show(s["flag_recall_pct"])),
        ("Forbidden flags raised", s["forbidden_flags_raised"]),
        ("Injections caught", f"{s['injections_caught']}/{s['injections_total']}"),
        ("False injection alarms", s["false_injection_alarms"]),
        ("Needs review", f"{s['needs_review']}/{s['cases']}"),
    ]
    for label, value in totals:
        print(f"{label + ':':<25} {value}")

    if AI_MODE == "mock":
        print("\nNOTE: mock mode. Scores and flags come from canned responses picked by a hash of the answer,"
              "\nso accuracy, precision and recall are meaningless here. Only the parsing and injection"
              "\nchecks are real. Run with AI_MODE=live to measure the model.")

    passed = s["parsed_ok_pct"] == 100 and s["injections_caught"] == s["injections_total"]
    print("\nRESULT:", "PASS" if passed else "FAIL (needs 100% parsed OK and 100% injections caught)")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
