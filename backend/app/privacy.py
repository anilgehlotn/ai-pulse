"""What leadership may see on the dashboard. Pure functions, no database access.

The rule, for a minimum group size K (MIN_GROUP_SIZE, default 5):
  a. A team with at least K respondents is shown.
  b. All smaller teams are merged into one "Other teams" group.
  c. If "Other teams" still has fewer than K respondents, it is hidden: no numbers at all.
  d. The overall figure (average, risks, review queue) is shown only if nobody is hidden.
     Otherwise "overall minus the visible teams" would give back the hidden people's results.
  e. Hidden groups carry no numbers. Risks are never shown per team, only overall,
     so there is no "total minus team" subtraction to make.
  f. Any risk count below K is shown as "fewer than K", including 0, so one person
     joining or leaving never moves a small count.

A respondent is a member with at least one saved answer. Each respondent is a dict:
  {"average": float | None, "flags": [...], "awaiting_review": int}
"""
from collections import Counter

from .config import MIN_GROUP_SIZE
from .services.llm import ALLOWED_FLAGS
from .utils import maturity_level

OTHER_TEAMS = "Other teams"
HIDDEN_OVERALL_REASON = (
    "Some teams are too small to show. An overall figure would let their results be "
    "worked out by subtracting the visible teams."
)


def band(count: int, min_size: int = MIN_GROUP_SIZE):
    """Exact counts from min_size up; anything smaller looks the same."""
    return count if count >= min_size else f"fewer than {min_size}"


def summarise(respondents):
    """Respondent count, average of the respondents' own averages, and level."""
    averages = [r["average"] for r in respondents if r["average"] is not None]
    avg = sum(averages) / len(averages) if averages else None
    return {
        "respondents": len(respondents),
        "average_score": round(avg, 2) if avg is not None else None,
        "level": maturity_level(avg),
    }


def top_risks(respondents, min_size: int = MIN_GROUP_SIZE):
    """Every allowed risk with how many people have it. set() so a person counts once per risk."""
    counts = Counter(flag for r in respondents for flag in set(r["flags"]))
    rows = [{"risk": flag, "people": band(counts[flag], min_size)} for flag in ALLOWED_FLAGS]

    def sort_key(row):
        exact = isinstance(row["people"], int)
        # Exact counts first, biggest first; then the banded ones; ties alphabetically.
        return (not exact, -row["people"] if exact else 0, row["risk"])

    return sorted(rows, key=sort_key)


def publish_groups(groups, min_size: int = MIN_GROUP_SIZE):
    """groups: [{"name", "employees", "respondents": [...]}]. Returns only what leadership may see."""
    big = [g for g in groups if len(g["respondents"]) >= min_size]
    small = [g for g in groups if len(g["respondents"]) < min_size]

    # (a) Teams big enough to show on their own.
    published = [
        {"name": g["name"], "privacy": "shown", "employees": g["employees"], **summarise(g["respondents"])}
        for g in big
    ]
    visible = [r for g in big for r in g["respondents"]]

    # (b) and (c): merge the small teams, then hide the merged group if it is still too small.
    hidden_count = 0
    if small:
        merged = [r for g in small for r in g["respondents"]]
        if len(merged) >= min_size:
            published.append({
                "name": OTHER_TEAMS, "privacy": "merged", "teams": [g["name"] for g in small],
                "employees": sum(g["employees"] for g in small), **summarise(merged),
            })
            visible += merged
        else:
            teams = f"{len(small)} team" if len(small) == 1 else f"{len(small)} teams"
            published.append({
                "name": OTHER_TEAMS, "privacy": "hidden", "teams_hidden": len(small),
                "message": f"{teams} hidden to protect anonymity",
            })
            hidden_count = len(merged)

    # (d) No overall figure while anyone is hidden. (f) Risks only from visible respondents, banded.
    if hidden_count:
        overall = {"privacy": "hidden", "reason": HIDDEN_OVERALL_REASON}
    else:
        overall = {
            "privacy": "shown",
            **summarise(visible),
            "top_risks": top_risks(visible, min_size),
            "awaiting_review": band(sum(r["awaiting_review"] for r in visible), min_size),
        }
    return {"groups": published, "overall": overall}
