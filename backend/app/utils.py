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
