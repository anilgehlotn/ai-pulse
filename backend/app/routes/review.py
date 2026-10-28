"""Human review of open answers the AI couldn't be trusted on (status "needs_review").

The reviewer sees the answer but never its author: no name, email, ids, team, job role or seniority.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..services.llm import ALLOWED_FLAGS, prepare_answer
from ..services.questions import load_questions
from ..services.scoring import ScoreResult, cap_for_data_risk

router = APIRouter(prefix="/review", tags=["review"])

HUMAN_REVIEWED = "human_reviewed"


class ReviewIn(BaseModel):
    # strict: "3", 3.5 and true are rejected instead of being turned into a number.
    score: int = Field(ge=1, le=5, strict=True)
    flags: list[str] = []


def reviewer_only(m: models.Membership = Depends(current_membership)) -> models.Membership:
    if m.role != "reviewer":
        raise HTTPException(403, "Reviewers only")
    return m


def waiting_answers(db: Session, reviewer: models.Membership):
    """Answers in the reviewer's organization that wait for a person, oldest first.

    Never the reviewer's own answers: they would recognise them and could raise their own score.
    """
    return (
        db.query(models.Response)
        .join(models.Membership, models.Response.membership_id == models.Membership.id)
        .filter(
            models.Membership.org_id == reviewer.org_id,
            models.Response.membership_id != reviewer.id,
            models.Response.status == "needs_review",
        )
        .order_by(models.Response.created_at, models.Response.id)
    )


@router.get("/queue")
def review_queue(m: models.Membership = Depends(reviewer_only), db: Session = Depends(get_db)):
    question_text = {q["id"]: q["text"] for q in load_questions()}
    # These are the only fields that leave the server. Nothing here says who wrote the answer.
    return [
        {
            "review_id": r.review_id,
            "question": question_text.get(r.question_id, r.question_id),
            "answer": prepare_answer(r.answer),  # emails and phone numbers removed
            "reason": r.reason,
            "flags": r.flags or [],
            "adjustments": r.adjustments or [],
            "possible_injection": r.reason == "possible_prompt_injection",
        }
        for r in waiting_answers(db, m)
    ]


@router.post("/{review_id}")
def submit_review(review_id: str, body: ReviewIn, m: models.Membership = Depends(reviewer_only),
                  db: Session = Depends(get_db)):
    # Checked before looking the answer up, so a bad request gets the same reply whether or not it exists.
    unknown = [f for f in body.flags if f not in ALLOWED_FLAGS]
    if unknown:
        raise HTTPException(422, f"Unknown flags: {', '.join(unknown)}")

    row = waiting_answers(db, m).filter(models.Response.review_id == review_id).first()
    # The same 404 whether it doesn't exist, was already reviewed or belongs to another organization.
    if row is None:
        raise HTTPException(404, "No answer with this id is waiting for review")

    # Same rule as the AI path: a data-sharing flag caps the score at 3.
    flags = list(dict.fromkeys(body.flags))  # drop duplicates, keep order
    result = cap_for_data_risk(ScoreResult(status="scored", score=body.score, reason=HUMAN_REVIEWED, flags=flags))

    # Only updates the row if it is still waiting, so two reviewers can't both score it.
    updated = (
        db.query(models.Response)
        .filter_by(id=row.id, status="needs_review")
        .update({
            "status": "scored",
            "score": result.score,
            "reason": HUMAN_REVIEWED,
            "flags": result.flags,
            "adjustments": (row.adjustments or []) + result.adjustments + [HUMAN_REVIEWED],
            "reviewed_at": models.utc_now(),
        })
    )
    if updated == 0:
        raise HTTPException(404, "No answer with this id is waiting for review")

    # One transaction: the new score and its accountability record are saved together, or neither is.
    db.add(models.ReviewEvent(review_id=row.review_id, reviewer_membership_id=m.id,
                              old_status="needs_review", new_score=result.score))
    db.commit()
    return {"review_id": row.review_id, "score": result.score, "flags": result.flags}
