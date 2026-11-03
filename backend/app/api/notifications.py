import uuid
import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models.job import NotificationLog, User
from backend.app.notifications.telegram import TelegramNotificationService
from backend.app.config import settings

from backend.app.api.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class TelegramTestRequest(BaseModel):
    chat_id: Optional[str] = None

@router.get("/logs")
async def list_notification_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationLog).where(NotificationLog.user_id == current_user.id)
    stmt = stmt.order_by(NotificationLog.sent_at.desc()).limit(50)

    res = await db.execute(stmt)
    logs = res.scalars().all()
    
    return {
        "success": True,
        "data": [
            {
                "id": l.id,
                "job_id": l.job_id,
                "channel": l.channel,
                "recipient": l.recipient,
                "status": l.status,
                "match_reason": l.match_reason,
                "sent_at": l.sent_at.isoformat() if l.sent_at else None
            }
            for l in logs
        ]
    }

@router.post("/telegram/token")
async def generate_telegram_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    PART 9 — Generate secure token for Telegram Bot account linking (/start TOKEN)
    """
    token = f"jp_tok_{uuid.uuid4().hex}"
    current_user.telegram_token = token
    await db.commit()

    return {
        "success": True,
        "token": token,
        "bot_username": settings.TELEGRAM_BOT_TOKEN.split(":")[0] if settings.TELEGRAM_BOT_TOKEN else "JobPulseBot",
        "instructions": f"Open Telegram, search for your bot, and send command: /start {token}"
    }

@router.post("/telegram/link")
async def link_telegram_account(
    token: str = Body(..., embed=True),
    chat_id: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    PART 9 — Validates token and completes Telegram account linking
    """
    if not token or not chat_id:
        raise HTTPException(status_code=400, detail="Invalid token or chat_id.")

    current_user.telegram_chat_id = chat_id
    current_user.telegram_connected = True
    await db.commit()

    return {
        "success": True,
        "message": "Telegram account linked successfully!",
        "data": {
            "telegram_chat_id": chat_id,
            "telegram_connected": True,
            "linked_at": datetime.datetime.utcnow().isoformat()
        }
    }

@router.post("/telegram/disconnect")
async def disconnect_telegram_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.telegram_chat_id = None
    current_user.telegram_connected = False
    current_user.telegram_token = None
    await db.commit()

    return {
        "success": True,
        "message": "Telegram account disconnected.",
        "data": {"telegram_connected": False}
    }


@router.post("/telegram/test")
async def send_telegram_test(
    payload: TelegramTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends a sample alert to the given chat ID (or the account's saved one). A successful
    delivery also saves that chat ID to the account, since the bot can only reach chats
    that have started a conversation with it.
    """
    chat_id = (payload.chat_id or current_user.telegram_chat_id or "").strip()
    if not chat_id:
        raise HTTPException(status_code=400, detail="Enter your Telegram chat ID first.")

    test_job = {
        "id": 999,
        "company": "JobPulse Engine",
        "title": "Software Development Engineer (SDE 1)",
        "location": "Bengaluru, India / Remote",
        "experience_level": "Fresher / 0-1 YOE",
        "salary_range": "₹12 - ₹18 LPA",
        "remote_type": "Remote",
        "job_url": "https://github.com/Sthitadhi1/JobPulse",
        "source": "JobPulse Core",
        "source_type": "ATS"
    }
    
    match_reasons = "• Python & FastAPI Stack\n• ₹12-18 LPA Target Salary\n• Remote Work Option"
    
    sent = await TelegramNotificationService.send_job_notification(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=chat_id,
        job=test_job,
        match_reasons=match_reasons
    )

    if sent:
        current_user.telegram_chat_id = chat_id
        current_user.telegram_connected = True
        await db.commit()

    return {
        "success": True,
        "message": "Test alert delivered. Your chat ID is saved for job alerts." if sent
                   else "Telegram did not accept the message. Start a chat with the bot first and check your chat ID.",
        "delivered_via_api": sent,
        "simulated_text": TelegramNotificationService.format_job_match_message(test_job, match_reasons)
    }
