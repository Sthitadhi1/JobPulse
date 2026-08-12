import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Header, Cookie

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


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

# Pydantic Request/Response Models
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)
    password: str

class ResendVerificationRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)

class RequestOtpRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)

class VerifyOtpRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)
    otp: str = Field(..., min_length=6, max_length=6)

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150)

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
    token = jobpulse_session
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
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
        email_verified=False
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate verification token
    raw_token, token_hash = AuthService.generate_token()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRY_HOURS)

    verif_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(verif_token)
    await db.commit()

    verif_link = f"http://localhost:8000/api/v1/auth/verify-email?token={raw_token}"
    EmailService.send_verification_email(user.email, verif_link)

    # Auto session login
    session_token, _ = await AuthService.create_user_session(db, user.id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=getattr(settings, "SECURE_COOKIES", False),
        max_age=7 * 86400
    )


    return {
        "success": True,
        "message": "User account created successfully. Verification email dispatched.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified
        }
    }


from sqlalchemy import select, delete

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
        max_age=7 * 86400
    )

    return {
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified
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


from fastapi.responses import HTMLResponse

@router.get("/verify-email")
async def verify_email(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    if not token:
        if "text/html" in request.headers.get("accept", ""):
            return HTMLResponse("<h2>Missing verification token.</h2><p><a href='/dashboard'>Return to JobPulse</a></p>")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing verification token.")

    token_hash = AuthService.hash_token(token)
    now = datetime.datetime.utcnow()

    res = await db.execute(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at == None
        )
    )
    verif_record = res.scalars().first()
    if not verif_record:
        if "text/html" in request.headers.get("accept", ""):
            return HTMLResponse("<h2>Invalid or already used verification token.</h2><p><a href='/dashboard'>Return to JobPulse</a></p>")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or already used verification token.")

    if verif_record.expires_at < now:
        if "text/html" in request.headers.get("accept", ""):
            return HTMLResponse("<h2>Verification token has expired.</h2><p><a href='/dashboard'>Return to JobPulse</a></p>")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired.")

    verif_record.used_at = now
    
    user_res = await db.execute(select(User).where(User.id == verif_record.user_id))
    user = user_res.scalars().first()
    if user:
        user.email_verified = True

    await db.commit()

    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head><title>JobPulse — Email Verified</title><style>body { font-family: sans-serif; background: #070a11; color: #f8fafc; text-align: center; padding: 60px 20px; } .card { max-width: 450px; margin: 0 auto; background: #0f172a; padding: 40px; border-radius: 12px; border: 1px solid #1e293b; } .btn { display: inline-block; padding: 12px 24px; background: #3b82f6; color: white; border-radius: 6px; text-decoration: none; font-weight: 600; margin-top: 20px; }</style></head>
            <body>
                <div class="card">
                    <h1>Email verified successfully.</h1>
                    <p>Your JobPulse account email has been verified.</p>
                    <a href="/dashboard" class="btn">Continue to JobPulse</a>
                </div>
            </body>
            </html>
        """)

    return {"success": True, "message": "Email address verified successfully."}


@router.post("/resend-verification")
async def resend_verification(req: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()

    # Generic response to prevent email enumeration
    if not user or user.email_verified:
        return {"success": True, "message": "If the account exists and is unverified, a verification link has been sent."}

    raw_token, token_hash = AuthService.generate_token()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRY_HOURS)

    verif_token = EmailVerificationToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(verif_token)
    await db.commit()

    verif_link = f"http://localhost:8000/api/v1/auth/verify-email?token={raw_token}"
    EmailService.send_verification_email(user.email, verif_link)

    return {"success": True, "message": "If the account exists and is unverified, a verification link has been sent."}


@router.post("/request-otp")
async def request_otp(req: RequestOtpRequest, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)

    # Check recent OTP rate limit (max 3 OTP requests per 10 minutes)
    now = datetime.datetime.utcnow()
    ten_mins_ago = now - datetime.timedelta(minutes=10)
    count_res = await db.execute(
        select(OtpRecord).where(
            OtpRecord.email == email,
            OtpRecord.created_at > ten_mins_ago
        )
    )
    recent_otps = count_res.scalars().all()
    if len(recent_otps) >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many OTP requests. Please wait a few minutes.")

    raw_otp, otp_hash = AuthService.generate_otp()
    expires_at = now + datetime.timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

    otp_record = OtpRecord(
        email=email,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0
    )
    db.add(otp_record)
    await db.commit()

    EmailService.send_otp_email(email, raw_otp)

    return {"success": True, "message": "If valid, a 6-digit OTP code has been sent to your email."}


@router.post("/verify-otp")
async def verify_otp(req: VerifyOtpRequest, response: Response, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active OTP found for this email.")

    if otp_record.attempts >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many failed attempts. Request a new OTP.")

    if otp_record.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired.")

    otp_record.attempts += 1

    if otp_record.otp_hash != otp_hash:
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP code.")

    otp_record.used_at = now

    # Fetch user & verify email
    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalars().first()
    if user:
        user.email_verified = True
        session_token, _ = await AuthService.create_user_session(db, user.id)
        response.set_cookie(
            key=COOKIE_NAME,
            value=session_token,
            httponly=True,
            samesite="lax",
            secure=getattr(settings, "SECURE_COOKIES", False),
            max_age=7 * 86400
        )

        await db.commit()
        return {
            "success": True,
            "message": "OTP verified successfully.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "email_verified": True
            }
        }

    await db.commit()
    return {"success": True, "message": "OTP verified successfully."}


@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = AuthService.normalize_email(req.email)
    res = await db.execute(select(User).where(User.email == email))
    user = res.scalars().first()

    # Generic response to prevent email enumeration
    if not user:
        return {"success": True, "message": "If an account with that email exists, a password reset link has been sent."}

    raw_token, token_hash = AuthService.generate_token()
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=2)

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(reset_record)
    await db.commit()

    reset_link = f"http://localhost:8000/api/v1/auth/reset-password?token={raw_token}"
    EmailService.send_password_reset_email(user.email, reset_link)

    return {"success": True, "message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_hash = AuthService.hash_token(req.token)
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

    # Invalidate all existing sessions for security
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))

    
    await db.commit()

    return {"success": True, "message": "Password reset successfully. Please log in with your new password."}


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not AuthService.verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password.")

    current_user.password_hash = AuthService.hash_password(req.new_password)
    await db.commit()

    return {"success": True, "message": "Password changed successfully."}


@router.get("/me")
async def me(current_user: Optional[User] = Depends(get_current_user_optional)):
    if not current_user:
        return {"authenticated": False, "user": None}

    return {
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "email_verified": current_user.email_verified,
            "is_active": current_user.is_active,
            "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }
