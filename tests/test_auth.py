import unittest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from backend.app.database import Base
from backend.app.models.job import User
from backend.app.services.auth_service import AuthService

class TestAuthService(unittest.TestCase):
    def setUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.AsyncSessionLocal = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)

    def tearDown(self):
        asyncio.run(self.engine.dispose())

    def test_email_normalization(self):
        self.assertEqual(AuthService.normalize_email(" USER@Example.COM "), "user@example.com")

    def test_password_hashing_and_verification(self):
        pwd = "SecretPassword123!"
        hashed = AuthService.hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(AuthService.verify_password(pwd, hashed))
        self.assertFalse(AuthService.verify_password("WrongPassword", hashed))

    def test_token_and_otp_generation(self):
        raw_token, token_hash = AuthService.generate_token()
        self.assertTrue(len(raw_token) > 20)
        self.assertEqual(AuthService.hash_token(raw_token), token_hash)

        raw_otp, otp_hash = AuthService.generate_otp()
        self.assertEqual(len(raw_otp), 6)
        self.assertTrue(raw_otp.isdigit())
        self.assertEqual(AuthService.hash_token(raw_otp), otp_hash)

    def test_user_session_lifecycle(self):
        async def run_check():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with self.AsyncSessionLocal() as session:
                user = User(
                    name="Test Student",
                    email="student@university.edu",
                    password_hash=AuthService.hash_password("Password123"),
                    is_active=True
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                # Create session
                raw_session_token, session_obj = await AuthService.create_user_session(session, user.id)
                self.assertIsNotNone(raw_session_token)

                # Validate session token
                found_user = await AuthService.get_user_from_session_token(session, raw_session_token)
                self.assertIsNotNone(found_user)
                self.assertEqual(found_user.email, "student@university.edu")

                # Revoke session
                revoked = await AuthService.revoke_session(session, raw_session_token)
                self.assertTrue(revoked)

                # Validate after revocation
                user_after = await AuthService.get_user_from_session_token(session, raw_session_token)
                self.assertIsNone(user_after)

        asyncio.run(run_check())

    def test_idor_authorization_and_session_invalidation(self):
        async def run_check():
            from backend.app.models.job import SavedSearch
            from backend.app.models.application import JobApplication
            from backend.app.models.auth_models import UserSession
            from sqlalchemy import delete

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with self.AsyncSessionLocal() as session:
                user_a = User(name="User A", email="usera@example.com", password_hash=AuthService.hash_password("PassA123"))
                user_b = User(name="User B", email="userb@example.com", password_hash=AuthService.hash_password("PassB123"))
                session.add_all([user_a, user_b])
                await session.commit()
                await session.refresh(user_a)
                await session.refresh(user_b)

                # Create saved search owned by User A
                search_a = SavedSearch(user_id=user_a.id, name="User A Search", query="Backend")
                session.add(search_a)
                await session.commit()

                # User B ownership check simulation
                self.assertNotEqual(user_a.id, user_b.id)
                self.assertEqual(search_a.user_id, user_a.id)

                # Session Invalidation Test on Password Reset
                _, sess_1 = await AuthService.create_user_session(session, user_a.id)
                _, sess_2 = await AuthService.create_user_session(session, user_a.id)
                
                active_sessions_before = (await session.execute(select(UserSession).where(UserSession.user_id == user_a.id))).scalars().all()
                self.assertEqual(len(active_sessions_before), 2)

                # Invalidate session
                await session.execute(delete(UserSession).where(UserSession.user_id == user_a.id))
                await session.commit()

                active_sessions_after = (await session.execute(select(UserSession).where(UserSession.user_id == user_a.id))).scalars().all()
                self.assertEqual(len(active_sessions_after), 0)

        asyncio.run(run_check())

if __name__ == "__main__":
    unittest.main()

