import re
import httpx
from typing import Optional, Dict, Any

class TelegramNotificationService:
    @staticmethod
    def escape_markdown(text: str) -> str:
        if not text:
            return ""
        # Telegram MarkdownV2 special characters
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', str(text))

    @classmethod
    def format_job_match_message(cls, job: Dict[str, Any], match_reasons: Optional[str] = None) -> str:
        """
        PART 10 — Telegram Notification Message Template
        """
        company = cls.escape_markdown(job.get("company", "Company"))
        title = cls.escape_markdown(job.get("title", "Software Role"))
        location = cls.escape_markdown(job.get("location", "India / Remote"))
        exp = cls.escape_markdown(job.get("experience_level", "Fresher / 0-1 YOE"))
        salary = cls.escape_markdown(job.get("salary_range", "Disclosed on Application"))
        remote = cls.escape_markdown(job.get("remote_type", "Hybrid"))
        
        apply_target = job.get("external_apply_url") or job.get("job_url") or job.get("url") or "#"

        reason_block = cls.escape_markdown(match_reasons) if match_reasons else "• Matched saved search criteria"

        msg = (
            f"🚀 *New Job Match*\n\n"
            f"*Company:* {company}\n"
            f"*Role:* {title}\n"
            f"*Location:* {location}\n"
            f"*Experience:* {exp}\n"
            f"*Salary:* {salary}\n"
            f"*Remote:* {remote}\n\n"
            f"*Matched because:*\n{reason_block}\n\n"
            f"👉 [Apply Directly Listing]({apply_target})"
        )
        return msg

    @classmethod
    async def send_job_notification(cls, bot_token: str, chat_id: str, job: Dict[str, Any], match_reasons: Optional[str] = None) -> bool:
        if not bot_token or not chat_id:
            return False

        message_text = cls.format_job_match_message(job, match_reasons)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": False
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                return res.status_code == 200
        except Exception:
            return False
