from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import delete, select

from mykhata_api.db import Budget, LoginSession, Statement, Transaction, User
from mykhata_api.deps import CurrentUser, Db
from mykhata_api.schemas import LoginIn, UserOut, UserPatch
from mykhata_api.security import hash_password, needs_rehash, new_token, token_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _start_session(request: Request, response: Response, db: Db, user: User) -> None:
    settings = request.app.state.settings
    token, hashed = new_token()
    expires = datetime.now(UTC) + timedelta(days=settings["session_days"])
    db.add(LoginSession(token_hash=hashed, user_id=user.id, expires_at=expires))
    db.commit()
    response.set_cookie(settings["cookie_name"], token, max_age=settings["session_days"] * 86400, httponly=True,
                        secure=settings["cookie_secure"], samesite="lax", path="/")


@router.post("/login", response_model=UserOut)
def login(body: LoginIn, request: Request, response: Response, db: Db) -> User:
    email = body.email.lower()
    limiter = request.app.state.login_limiter
    key = f"{request.client.host if request.client else '-'}|{email}"
    if not limiter.allow(key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Wait a few minutes and try again.")
    user = db.scalar(select(User).where(User.email == email))
    if not verify_password(body.password, user.password_hash if user else None):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect.")
    limiter.reset(key)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    _start_session(request, response, db, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Db) -> None:
    name = request.app.state.settings["cookie_name"]
    if token := request.cookies.get(name):
        db.execute(delete(LoginSession).where(LoginSession.token_hash == token_hash(token)))
        db.commit()
    response.delete_cookie(name, path="/")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: UserPatch, user: CurrentUser, db: Db) -> User:
    if body.name is not None:
        user.name = body.name.strip()
    if body.confidence_threshold is not None:
        user.confidence_threshold = round(body.confidence_threshold, 2)
    db.commit()
    return user


@router.delete("/me/data", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_data(user: CurrentUser, db: Db) -> None:
    for model in (Transaction, Statement, Budget):
        db.execute(delete(model).where(model.user_id == user.id))
    db.commit()
