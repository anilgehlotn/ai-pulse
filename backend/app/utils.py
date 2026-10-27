from .services.profile import dimension_scores


def maturity_level(avg_score):
    """Turn an average on the 1-5 rubric into a level. The single scale for reports and the dashboard.

    The rubric: 1 = no AI use, 2 = occasional basic use, 3 = regular use for simple tasks,
    4 = regular, thoughtful use with review, 5 = advanced use that changes the work.
    A level is reached only once the average gets to that rubric point:
    below 2 = Beginner, 2 to <3 = Exploring, 3 to <4 = Practitioner, 4 and above = Leader.
    """
    if avg_score is None:
        return "Not assessed"
    if avg_score < 2:
        return "Beginner"
    if avg_score < 3:
        return "Exploring"
    if avg_score < 4:
        return "Practitioner"
    return "Leader"


def person_summary(rows):
    """One person's saved answers -> their average, risk flags, number of answers awaiting review,
    and their adoption and safety scores.

    Answers awaiting review count as answered but never towards the average or the flags.
    """
    trusted = [r for r in rows if r.status != "needs_review"]
    scores = [r.score for r in trusted if r.score is not None]
    return {
        "average": sum(scores) / len(scores) if scores else None,
        "flags": sorted({f for r in trusted for f in (r.flags or [])}),
        "awaiting_review": len(rows) - len(trusted),
        **dimension_scores(trusted),
    }


def rounded(value):
    return round(value, 2) if value is not None else None
