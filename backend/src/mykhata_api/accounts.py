from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from mykhata_api.db import LoginSession, User
from mykhata_api.security import hash_password

MIN_PASSWORD = 8


def upsert_user(db: Session, email: str, password: str, name: str | None = None) -> tuple[User, bool]:
    """Create the account, or reset its password (signing out every session). Returns (user, created)."""
    if not 8 <= len(password) <= 128:
        raise ValueError("Use a password of 8 to 128 characters.")
    email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    created = user is None
    if created:
        user = User(email=email, name=(name or email.split("@")[0]).strip(), password_hash=hash_password(password))
        db.add(user)
    else:
        user.password_hash = hash_password(password)
        if name:
            user.name = name.strip()
        db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    db.commit()
    return user, created
