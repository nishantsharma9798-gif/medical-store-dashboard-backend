import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User, RoleEnum
from app.db.models.client import Client
from app.core.config import settings
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    decode_token,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserOut,
    SignupRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.email import send_email, build_reset_password_email

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

REFRESH_COOKIE_MAX_AGE = 7 * 24 * 60 * 60


def _issue_session(user: User, response: Response) -> LoginResponse:
    access_token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    refresh_token = create_refresh_token(subject=str(user.id))

    # Store both tokens in cookies so browser sessions work reliably over localhost HTTP.
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.jwt_access_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )
    return LoginResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    return _issue_session(user, response)


@router.post("/signup", response_model=LoginResponse)
def signup(payload: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """Creates a new Client (business) plus its first Client Admin user, then logs them in."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists")

    client = Client(id=uuid.uuid4(), name=payload.business_name, enabled_apps=["medical"])
    db.add(client)
    db.flush()  # get client.id without a full commit yet

    user = User(
        id=uuid.uuid4(),
        client_id=client.id,
        name=payload.admin_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=RoleEnum.client_admin,
        permissions=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_session(user, response)


@router.post("/refresh")
def refresh(response: Response, refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_access_token = create_access_token(subject=payload["sub"])
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.jwt_access_expire_minutes * 60,
    )
    return {"accessToken": new_access_token}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"detail": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Always returns a generic success message — whether or not the email exists —
    so this endpoint can't be used to check which emails are registered.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        reset_token = create_password_reset_token(subject=str(user.id))
        subject, body = build_reset_password_email(reset_token)
        await send_email(to=user.email, subject=subject, body=body)

    return {"detail": "If an account exists for this email, a reset link has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.token)
        if decoded.get("type") != "reset":
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    try:
        user_id = uuid.UUID(decoded["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset link")

    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password reset successfully"}
