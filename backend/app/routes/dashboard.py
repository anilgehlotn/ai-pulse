from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..config import MIN_GROUP_SIZE
from ..privacy import publish_groups
from ..utils import person_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

UNASSIGNED = "Unassigned"


def load_groups(db: Session, org: models.Organization):
    """Every team with its headcount and one summary per respondent.

    This is raw, identifiable data. Never return it directly: it must go through publish_groups.
    """
    members = db.query(models.Membership).filter_by(org_id=org.id).all()
    # All responses for the organization in one query, then grouped per person.
    responses = (
        db.query(models.Response)
        .join(models.Membership, models.Response.membership_id == models.Membership.id)
        .filter(models.Membership.org_id == org.id)
        .all()
    )
    rows_by_member = defaultdict(list)
    for r in responses:
        rows_by_member[r.membership_id].append(r)

    teams = [(dept.name, [x for x in members if x.department_id == dept.id]) for dept in org.departments]
    unassigned = [x for x in members if x.department_id is None]
    if unassigned:
        teams.append((UNASSIGNED, unassigned))

    # A respondent is a member with at least one saved answer.
    return [
        {
            "name": name,
            "employees": len(people),
            "respondents": [person_summary(rows_by_member[p.id]) for p in people if p.id in rows_by_member],
        }
        for name, people in teams
    ]


@router.get("")
def org_dashboard(m: models.Membership = Depends(current_membership), db: Session = Depends(get_db)):
    if m.role != "admin":
        raise HTTPException(403, "Admins only")

    # The organization always comes from the signed token, never from the request.
    # Every number below comes out of publish_groups, the single place the anonymity rule is applied.
    return {
        "organization": m.org.name,
        "min_group_size": MIN_GROUP_SIZE,
        **publish_groups(load_groups(db, m.org)),
    }
