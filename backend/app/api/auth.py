import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header, Cookie
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from backend.app.database import get_db
from backend.app.models.job import User
from backend.app.models.auth_models import (
    EmailVerificationToken,
    PasswordResetToken,
    OtpRecord,
    UserSession
)
from backend.app.services.auth_service import AuthService
from backend.app.services.email_service import EmailService
from backend.app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

COOKIE_NAME = "jobpulse_session"

# Pydantic Request Models
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)

class ResetPasswordOtpRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=100)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


# Fast Helper Dependency for Current Authenticated User
async def get_current_user_optional(
    request: Request,
    jobpulse_session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
    if not token and jobpulse_session:
        token = jobpulse_session.strip()
    if not token:
        # Also check custom header
        custom_token = request.headers.get("X-JobPulse-Token")
        if custom_token:
            token = custom_token.strip()

    if not token:
        return None
    return await AuthService.get_user_from_session_token(db, token)

async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )
    return user


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(req: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)

    res = await db.execute(select(User).where(User.email == email))
    if res.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

    pwd_hash = AuthService.hash_password(req.password)

    user = User(
        name=req.name.strip(),
        email=email,
        password_hash=pwd_hash,
        is_active=True,
        email_verified=True # Auto-verified for instant onboarding
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Auto session login
    session_token, _ = await AuthService.create_user_session(db, user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=getattr(settings, "SECURE_COOKIES", False),
        max_age=14 * 86400
    )

    return {
        "success": True,
        "message": "User account created successfully.",
        "token": session_token,
        "session_token": session_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified
        }
    }


@router.post("/login")
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()

    if not user or not AuthService.verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    user.last_login_at = datetime.datetime.utcnow()

    # Session Fixation Protection: Invalidate previous active sessions for this user
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))

    session_token, _ = await AuthService.create_user_session(db, user.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=getattr(settings, "SECURE_COOKIES", False),
        max_age=14 * 86400
    )

    return {
        "success": True,
        "message": "Login successful.",
        "token": session_token,
        "session_token": session_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified
        }
    }


@router.get("/me")
async def get_me(current_user: Optional[User] = Depends(get_current_user_optional)):
    if not current_user:
        return {"authenticated": False, "user": None}
    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "email_verified": current_user.email_verified,
            "telegram_connected": current_user.telegram_connected,
            "telegram_chat_id": current_user.telegram_chat_id
        }
    }


@router.post("/logout")
async def logout(
    response: Response,
    jobpulse_session: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    token = jobpulse_session
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    
    if token:
        await AuthService.revoke_session(db, token)

    response.delete_cookie(key=COOKIE_NAME)
    return {"success": True, "message": "Logged out successfully."}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()

    if not user:
        # Prevent email enumeration while giving a clear message
        return {
            "success": True,
            "message": "If an account with that email exists, a password reset code has been issued."
        }

    raw_otp, otp_hash = AuthService.generate_otp()
    raw_token, token_hash = AuthService.generate_token()
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(hours=2)

    # Store OTP record
    otp_record = OtpRecord(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0
    )
    db.add(otp_record)

    # Store token record
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(reset_record)
    await db.commit()

    # Attempt to send email
    reset_link = f"/dashboard/?reset_token={raw_token}"
    EmailService.send_password_reset_email(user.email, reset_link)

    return {
        "success": True,
        "message": f"Password reset code generated. Use code {raw_otp} to set a new password.",
        "otp_code": raw_otp,
        "reset_token": raw_token
    }


@router.post("/reset-password-otp")
async def reset_password_otp(req: ResetPasswordOtpRequest, response: Response, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)
    otp_hash = AuthService.hash_token(req.otp.strip())
    now = datetime.datetime.utcnow()

    res = await db.execute(
        select(OtpRecord).where(
            OtpRecord.email == email,
            OtpRecord.used_at == None
        ).order_by(OtpRecord.id.desc())
    )
    otp_record = res.scalars().first()

    if not otp_record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active reset code found for this email.")

    if otp_record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset code has expired.")

    if otp_record.otp_hash != otp_hash:
        otp_record.attempts += 1
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset code.")

    otp_record.used_at = now

    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    user.password_hash = AuthService.hash_password(req.new_password)

    # Invalidate all prior sessions
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))

    # Auto-login with new session
    session_token, _ = await AuthService.create_user_session(db, user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=getattr(settings, "SECURE_COOKIES", False),
        max_age=14 * 86400
    )

    await db.commit()

    return {
        "success": True,
        "message": "Password reset successfully! Logged in.",
        "token": session_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, response: Response, db: AsyncSession = Depends(get_db)):
    token_hash = AuthService.hash_token(req.token.strip())
    now = datetime.datetime.utcnow()

    res = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at == None
        )
    )
    reset_record = res.scalars().first()

    if not reset_record or reset_record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")

    reset_record.used_at = now

    user_res = await db.execute(select(User).where(User.id == reset_record.user_id))
    user = user_res.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    user.password_hash = AuthService.hash_password(req.new_password)

    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    session_token, _ = await AuthService.create_user_session(db, user.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=getattr(settings, "SECURE_COOKIES", False),
        max_age=14 * 86400
    )

    await db.commit()

    return {
        "success": True,
        "message": "Password reset successfully! Logged in.",
        "token": session_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not AuthService.verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect.")

    current_user.password_hash = AuthService.hash_password(req.new_password)
    await db.commit()

    return {"success": True, "message": "Password updated successfully."}
