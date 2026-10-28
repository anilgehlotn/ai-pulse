from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models
from ..auth import DUMMY_PASSWORD_HASH, verify_password, make_token, current_user, selected_org_id
from ..rate_limit import login_limiter, too_many_attempts_message

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class SelectOrgIn(BaseModel):
    org_id: int


def organizations_of(user: models.User):
    return [{"org_id": m.org_id, "org_name": m.org.name, "role": m.role} for m in user.memberships]


@router.post("/login")
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    # The limit is per email (lower-cased, registered or not) and per IP. See app/rate_limit.py.
    email_key = body.email.strip().lower()
    # The address that actually connected. We don't read X-Forwarded-For: the caller writes that header,
    # so an attacker could put a new IP in it on every request. Behind a proxy or load balancer, configure
    # its address as trusted (for example uvicorn --proxy-headers --forwarded-allow-ips) instead.
    ip = request.client.host if request.client else "unknown"
    wait = login_limiter.seconds_to_wait(email_key, ip)
    if wait:
        raise HTTPException(429, too_many_attempts_message(wait), headers={"Retry-After": str(wait)})
    login_limiter.record_attempt(ip)

    user = db.query(models.User).filter_by(email=body.email).first()
    # Always run one bcrypt check, even for unknown emails, so timing doesn't reveal who is registered.
    password_ok = verify_password(body.password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if not user or not password_ok:
        login_limiter.record_failure(email_key)
        raise HTTPException(401, "Wrong email or password")
    login_limiter.record_success(email_key)
    return {"token": make_token(user.id), "name": user.name, "organizations": organizations_of(user)}


@router.get("/me")
def me(user: models.User = Depends(current_user), org_id: int | None = Depends(selected_org_id)):
    """Who is signed in. Lets the frontend restore the session after a page refresh."""
    orgs = organizations_of(user)
    # Only an organization the user still belongs to counts as selected.
    selected = next((o for o in orgs if o["org_id"] == org_id), None)
    return {"name": user.name, "email": user.email, "organizations": orgs, "selected_org": selected}


@router.post("/select-org")
def select_org(body: SelectOrgIn, user: models.User = Depends(current_user), db: Session = Depends(get_db)):
    membership = db.query(models.Membership).filter_by(user_id=user.id, org_id=body.org_id).first()
    if not membership:
        raise HTTPException(403, "Not a member of this organization")
    # Issue a token scoped to the chosen organization
    return {"token": make_token(user.id, body.org_id), "org_id": body.org_id}
