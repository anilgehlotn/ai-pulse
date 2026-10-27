import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "questions.json")

# Seniority levels in order. Compare ranks, never the strings ("lead" < "mid" alphabetically).
SENIORITY_RANK = {"junior": 0, "mid": 1, "senior": 2, "lead": 3}


def load_questions():
    with open(_PATH) as f:
        return json.load(f)


def seniority_rank(seniority: str) -> int:
    if seniority not in SENIORITY_RANK:
        raise ValueError(f"Unknown seniority '{seniority}', expected one of {list(SENIORITY_RANK)}")
    return SENIORITY_RANK[seniority]


def questions_for(job_role: str, seniority: str):
    """Common questions for everyone + questions for this job role, filtered by seniority."""
    rank = seniority_rank(seniority)
    result = []
    for q in load_questions():
        if q["roles"] != ["all"] and job_role not in q["roles"]:
            continue
        if rank < seniority_rank(q.get("min_seniority", "junior")):
            continue
        result.append(q)
    return result
