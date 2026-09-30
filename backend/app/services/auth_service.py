from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User


def prepare_user_password(password: str) -> str:
    """
    Hash a user's password before it is stored.
    """
    return hash_password(password)


def create_user_token(email: str) -> str:
    """
    Create a JWT access token for a user.
    """
    return create_access_token(email)


def build_user(
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    """
    Build a User model with a securely hashed password.
    """
    return User(
        email=email,
        hashed_password=prepare_user_password(password),
        full_name=full_name,
    )
def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str | None = None,
) -> User:
    user = build_user(
        email=email,
        password=password,
        full_name=full_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """
    Find a user by email.
    """
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """
    Find a user and verify the provided password.
    """
    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user