from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.security import decode_token
from app.db.session import get_db
from app.db.models.user import User


def get_bearer_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
    access_token: str | None = Cookie(default=None, alias="access_token"),
) -> str:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token

    if access_token:
        return access_token

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


def get_current_user(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def auth_required() -> User:
    return Depends(get_current_user)


def require_role(*allowed_roles: str):
    """Dependency factory — e.g. Depends(require_role('client_admin', 'staff'))"""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user

    return checker
