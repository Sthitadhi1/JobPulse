from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models.job import NotificationLog, Job
from backend.app.notifications.telegram import TelegramNotifier

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class TelegramTestRequest(BaseModel):
    chat_id: str

@router.get("")
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(NotificationLog, Job).join(Job, NotificationLog.job_id == Job.id).order_by(NotificationLog.sent_at.desc()).limit(limit)
    res = await db.execute(stmt)
    records = res.all()

    notif_list = []
    for n_log, job in records:
        notif_list.append({
            "id": n_log.id,
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": job.salary_range,
            "channel": n_log.channel,
            "recipient": n_log.recipient,
            "status": n_log.status,
            "match_reason": n_log.match_reason,
            "apply_url": job.apply_url,
            "sent_at": n_log.sent_at.isoformat() if n_log.sent_at else None
        })

    return {
        "success": True,
        "message": "Notifications fetched.",
        "data": notif_list
    }

@router.post("/telegram/test")
async def send_test_telegram(body: TelegramTestRequest):
    sample_job = {
        "company": "JobPulse Engine",
        "title": "Software Development Engineer 1 (SDE I)",
        "location": "Bengaluru (Hybrid)",
        "salary_range": "₹12 - ₹16 LPA",
        "experience_level": "Fresh Graduate",
        "url": "https://github.com",
        "source": "Telegram Verification Bot"
    }
    reason = " • Exact title match: Software Engineer\n • Target salary: ₹8-15 LPA\n • Remote preference: Hybrid"
    msg = TelegramNotifier.format_job_message(sample_job, reason)
    success = await TelegramNotifier.send_message(body.chat_id, msg)

    return {
        "success": success,
        "message": f"Test alert {'delivered' if success else 'failed'}.",
        "data": {"chat_id": body.chat_id, "channel": "Telegram"}
    }
