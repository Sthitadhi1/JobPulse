from typing import Dict, Any
from backend.app.notifications.telegram import TelegramNotifier

class NotificationDispatcher:
    @classmethod
    async def dispatch(cls, channel: str, recipient: str, payload: Dict[str, Any], match_reason: str = None) -> bool:
        if channel.lower() == "telegram":
            msg = TelegramNotifier.format_job_message(payload, match_reason)
            return await TelegramNotifier.send_message(recipient, msg)
        return False
