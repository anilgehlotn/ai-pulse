from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..utils import maturity_level

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

UNASSIGNED = "Unassigned"


def department_row(name, employees, respondent_averages):
    """One dashboard row. Every respondent counts once, however many questions they answered."""
    avg = sum(respondent_averages) / len(respondent_averages) if respondent_averages else None
    return {
        "department": name,
        "employees": employees,
        "responded": len(respondent_averages),
        "average_score": round(avg, 2) if avg is not None else None,
        "level": maturity_level(avg),
    }


@router.get("")
def org_dashboard(m: models.Membership = Depends(current_membership), db: Session = Depends(get_db)):
    if m.role != "admin":
        raise HTTPException(403, "Admins only")

    # The organization always comes from the signed token, never from the request.
    org = m.org
    members = db.query(models.Membership).filter_by(org_id=org.id).all()

    # All responses for the organization in one query, then grouped per person.
    responses = (
        db.query(models.Response)
        .join(models.Membership, models.Response.membership_id == models.Membership.id)
        .filter(models.Membership.org_id == org.id)
        .all()
    )
    scores_by_member = defaultdict(list)
    flags_by_member = defaultdict(set)
    for r in responses:
        if r.score is not None:
            scores_by_member[r.membership_id].append(r.score)
        flags_by_member[r.membership_id].update(r.flags or [])
    average_by_member = {mid: sum(s) / len(s) for mid, s in scores_by_member.items()}

    groups = [(dept.name, [x for x in members if x.department_id == dept.id]) for dept in org.departments]
    unassigned = [x for x in members if x.department_id is None]
    if unassigned:
        groups.append((UNASSIGNED, unassigned))

    departments = [
        department_row(name, len(people), [average_by_member[p.id] for p in people if p.id in average_by_member])
        for name, people in groups
    ]

    # A set per person, so someone flagged in two answers counts once.
    risk_counts = Counter(flag for flags in flags_by_member.values() for flag in flags)
    # Most people first; ties alphabetically so the order is the same on every request.
    top_risks = sorted(risk_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]

    return {
        "organization": org.name,
        "departments": departments,
        "top_risks": top_risks,
    }
