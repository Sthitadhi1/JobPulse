import httpx
from typing import Dict, Any, Optional
from backend.app.config import settings

class TelegramNotifier:
    @classmethod
    def format_job_message(cls, job: Dict[str, Any], match_reason: Optional[str] = None) -> str:
        company = job.get("company", "Company")
        title = job.get("title", "Role")
        location = job.get("location", "Location")
        salary = job.get("salary_range", "Salary Disclosed on Application")
        exp = job.get("experience_level", "Fresh Graduate")
        url = job.get("url") or job.get("apply_url", "#")
        source = job.get("source", "JobPulse")

        msg = (
            f"🚀 **New Job Opportunity Discovered!**\n\n"
            f"🏢 **Company:** {company}\n"
            f"💼 **Role:** {title}\n"
            f"📍 **Location:** {location}\n"
            f"💰 **Salary:** {salary}\n"
            f"🎯 **Experience:** {exp}\n"
            f"⚡ **Source:** {source}\n\n"
        )

        if match_reason:
            msg += f"💡 **Why it matched:**\n{match_reason}\n\n"

        msg += f"🔗 [Apply Directly on Official Site]({url})\n\n"
        msg += "_JobPulse — Human-in-the-loop Job Discovery Engine_"
        return msg

    @classmethod
    async def send_message(cls, chat_id: str, message_text: str) -> bool:
        if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN == "MOCK_TELEGRAM_BOT_TOKEN":
            # Log simulated message in dev mode
            print(f"[MOCK TELEGRAM DISPATCH] To Chat ID: {chat_id}\n{message_text}")
            return True

        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json={
                    "chat_id": chat_id,
                    "text": message_text,
                    "parse_mode": "Markdown"
                })
                return res.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM DISPATCH ERROR] {str(e)}")
            return False
