"""Adoption vs safety: how much someone uses AI, kept apart from how safely they use it.

One average hides the riskiest pattern: heavy AI use without review or data care can average
the same as a careful team. So every MCQ question is tagged "adoption" or "safety" in
questions.json, and each dimension gets its own score. Open answers have no dimension.
"""
from .questions import load_questions

# A score of 3 is "regular use" on the 1-5 rubric: at or above it counts as high on that axis.
QUADRANT_THRESHOLD = 3

QUADRANT_EXPLANATIONS = {
    "Leading": "You use AI regularly and keep the safeguards in place, so share what works with your team.",
    "Exposed": "You use AI a lot, but your safety habits have not kept up, which is where mistakes and data leaks happen.",
    "Cautious": "Your safety habits are solid, so you are ready to use AI for more of your work.",
    "Getting started": "You are early on both, so build one safe habit first and then try AI on a small task.",
    None: "Answer both the usage and the safety questions to see where you stand.",
}

# One tip per safety question. The order is also the tie-break for the weakest habit:
# the habit that can do the most direct harm comes first.
SAFETY_TIPS = {
    "common-data": "Before pasting anything into an AI tool, remove names, emails and account numbers, "
                   "and use only approved tools.",
    "common-review": "Check every fact, number and name in an AI answer against a source before you use it.",
    "eng-review": "Read every line of AI-written code and add a test for it before it ships.",
    "common-policy": "Read your company's AI policy and note which tools are approved and what data you may share.",
    "mgr-policy": "Walk your team through the company AI policy using one real example from your own work.",
}

# question id -> "adoption" or "safety", for MCQ questions only.
DIMENSION_OF = {q["id"]: q["dimension"] for q in load_questions() if q["type"] == "mcq"}


def mcq_scores(rows, dimension):
    """question id -> score, for one person's MCQ answers in one dimension."""
    return {r.question_id: r.score for r in rows
            if r.status == "mcq" and r.score is not None and DIMENSION_OF.get(r.question_id) == dimension}


def average(values):
    return sum(values) / len(values) if values else None


def dimension_scores(rows):
    """One person's saved answers -> their adoption and safety averages (None if no answers in it)."""
    return {
        "adoption": average(list(mcq_scores(rows, "adoption").values())),
        "safety": average(list(mcq_scores(rows, "safety").values())),
    }


def quadrant(adoption, safety):
    """Place a person or group on the two axes. None if either score is missing.

    Callers pass the rounded scores they publish, so the label always matches the numbers shown.
    """
    if adoption is None or safety is None:
        return None
    uses_ai = adoption >= QUADRANT_THRESHOLD
    safe = safety >= QUADRANT_THRESHOLD
    if uses_ai and safe:
        return "Leading"
    if uses_ai:
        return "Exposed"
    if safe:
        return "Cautious"
    return "Getting started"


def weakest_safety_habit(rows):
    """The person's lowest-scoring safety question, or None. Ties go to the earlier one in SAFETY_TIPS."""
    scores = mcq_scores(rows, "safety")
    answered = [qid for qid in SAFETY_TIPS if qid in scores]
    # min() returns the first of equal values, so the SAFETY_TIPS order breaks ties.
    return min(answered, key=lambda qid: scores[qid]) if answered else None
