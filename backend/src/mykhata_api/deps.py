from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from mykhata_api.db import LoginSession, User, sessions
from mykhata_api.security import token_hash

CSRF_HEADER = "x-mykhata-request"


def get_db(request: Request) -> Iterator[Session]:
    yield from sessions(request.app.state.sessionmaker)


Db = Annotated[Session, Depends(get_db)]


def current_user(request: Request, db: Db) -> User:
    name = request.app.state.settings["cookie_name"]
    token = request.cookies.get(name)
    if token:
        session = db.get(LoginSession, token_hash(token))
        if session and session.expires_at.replace(tzinfo=UTC) > datetime.now(UTC):
            user = db.get(User, session.user_id)
            if user:
                return user
        clear = {"set-cookie": f"{name}=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax"}
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has expired. Please log in again.", headers=clear)
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in")


CurrentUser = Annotated[User, Depends(current_user)]
