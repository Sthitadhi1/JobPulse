import secrets
import hashlib
import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["argon2", "bcrypt", "pbkdf2_sha256"], deprecated="auto")
except Exception:
    pwd_context = None

from backend.app.config import settings
from backend.app.models.job import User
from backend.app.models.auth_models import (
    EmailVerificationToken,
    PasswordResetToken,
    OtpRecord,
    UserSession
)

class AuthService:
    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def hash_password(password: str) -> str:
        if pwd_context:
            try:
                return pwd_context.hash(password)
            except Exception:
                pass
        # Fallback PBKDF2 HMAC SHA256 (600,000 iterations per OWASP recommendation)
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 600000).hex()
        return f"pbkdf2_sha256${salt}${hashed}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if pwd_context and not hashed_password.startswith("pbkdf2_sha256$"):
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                pass
        if hashed_password.startswith("pbkdf2_sha256$"):
            try:
                parts = hashed_password.split("$")
                salt = parts[1]
                expected_hash = parts[2]
                computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 600000).hex()
                return secrets.compare_digest(computed, expected_hash)
            except Exception:
                return False
        return False


    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_token() -> Tuple[str, str]:
        """Returns (raw_token, token_hash)"""
        raw_token = secrets.token_urlsafe(32)
        token_hash = AuthService.hash_token(raw_token)
        return raw_token, token_hash

    @staticmethod
    def generate_otp() -> Tuple[str, str]:
        """Returns (raw_6_digit_otp, otp_hash)"""
        otp_num = secrets.randbelow(900000) + 100000
        raw_otp = str(otp_num)
        otp_hash = AuthService.hash_token(raw_otp)
        return raw_otp, otp_hash

    @classmethod
    async def create_user_session(cls, db: AsyncSession, user_id: str) -> Tuple[str, UserSession]:
        raw_token, token_hash = cls.generate_token()
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=7)
        
        session = UserSession(
            user_id=user_id,
            session_token_hash=token_hash,
            expires_at=expires_at,
            last_accessed_at=datetime.datetime.utcnow()
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return raw_token, session

    @classmethod
    async def get_user_from_session_token(cls, db: AsyncSession, session_token: str) -> Optional[User]:
        if not session_token:
            return None
        token_hash = cls.hash_token(session_token)
        now = datetime.datetime.utcnow()

        res = await db.execute(
            select(UserSession).where(
                UserSession.session_token_hash == token_hash,
                UserSession.expires_at > now
            )
        )
        session = res.scalars().first()
        if not session:
            return None

        # Update last accessed timestamp
        session.last_accessed_at = now
        await db.commit()

        user_res = await db.execute(select(User).where(User.id == session.user_id))
        return user_res.scalars().first()

    @classmethod
    async def revoke_session(cls, db: AsyncSession, session_token: str) -> bool:
        if not session_token:
            return False
        token_hash = cls.hash_token(session_token)
        res = await db.execute(select(UserSession).where(UserSession.session_token_hash == token_hash))
        session = res.scalars().first()
        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False
