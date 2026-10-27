from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import current_user

router = APIRouter(prefix="/me", tags=["me"])

CONFIRM_WORD = "DELETE"


class DeleteDataIn(BaseModel):
    confirm: str = ""  # missing counts as not confirmed (400), same as a wrong word


@router.delete("/data")
def delete_my_data(body: DeleteDataIn | None = None, user: models.User = Depends(current_user),
                   db: Session = Depends(get_db)):
    """Delete every answer this user has given, in every organization. The account itself stays.

    Dashboards and reports are computed from the database on every request, so the
    answers disappear from them as soon as this commits.
    """
    if body is None or body.confirm != CONFIRM_WORD:
        raise HTTPException(400, f'Send {{"confirm": "{CONFIRM_WORD}"}} to delete all your answers')

    # One transaction: all memberships are cleared and the event is logged, or nothing is.
    deleted = {}
    for m in user.memberships:
        deleted[m.org.name] = db.query(models.Response).filter_by(membership_id=m.id).delete()
    total = sum(deleted.values())
    db.add(models.DeletionEvent(answers_deleted=total))
    db.commit()
    return {"deleted_answers": deleted, "total": total}
