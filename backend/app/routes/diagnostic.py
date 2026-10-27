from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_membership
from ..services.questions import questions_for
from ..services.scoring import score_open_answer

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])

MAX_ANSWER_LENGTH = 2000


class AnswerIn(BaseModel):
    question_id: str
    answer: str = Field(max_length=MAX_ANSWER_LENGTH)


class SubmitIn(BaseModel):
    answers: list[AnswerIn]


@router.get("/questions")
def get_questions(m: models.Membership = Depends(current_membership)):
    qs = questions_for(m.job_role, m.seniority)
    # don't leak scoring points to the client
    return [
        {k: v for k, v in q.items() if k != "points"} | (
            {"options": [o["text"] for o in q["options"]]} if q["type"] == "mcq" else {}
        )
        for q in qs
    ]


@router.post("/submit")
def submit(body: SubmitIn, m: models.Membership = Depends(current_membership), db: Session = Depends(get_db)):
    assigned = {q["id"]: q for q in questions_for(m.job_role, m.seniority)}
    check_answers_match_questions([a.question_id for a in body.answers], assigned)

    # Build and score every answer before touching the database.
    new_rows = []
    for a in body.answers:
        q = assigned[a.question_id]
        resp = models.Response(membership_id=m.id, question_id=q["id"])
        if q["type"] == "mcq":
            option = next((o for o in q["options"] if o["text"] == a.answer), None)
            if option is None:
                raise HTTPException(400, f"Invalid option for {q['id']}")
            resp.answer = a.answer
            resp.score = option["points"]
        else:
            text = a.answer.strip()
            if not text:
                raise HTTPException(400, f"Answer for {q['id']} cannot be empty")
            result = score_open_answer(q["text"], text)
            resp.answer = text
            resp.score = result["score"]
            resp.reason = result["reason"]
            resp.flags = result["flags"]
        new_rows.append(resp)

    # Replace the previous attempt: delete and insert in one transaction, so either both happen or neither.
    # If anything above raised, we never get here and the session is rolled back when it closes.
    db.query(models.Response).filter_by(membership_id=m.id).delete()
    db.add_all(new_rows)
    db.commit()
    return {"saved": len(new_rows)}


def check_answers_match_questions(answered_ids, assigned):
    """Each assigned question must be answered exactly once, and nothing else."""
    not_assigned = sorted(set(answered_ids) - set(assigned))
    if not_assigned:
        raise HTTPException(400, f"Questions not assigned to you: {', '.join(not_assigned)}")
    duplicates = sorted({qid for qid in answered_ids if answered_ids.count(qid) > 1})
    if duplicates:
        raise HTTPException(400, f"Duplicate answers for: {', '.join(duplicates)}")
    missing = [qid for qid in assigned if qid not in answered_ids]
    if missing:
        raise HTTPException(400, f"Missing answers for: {', '.join(missing)}")
