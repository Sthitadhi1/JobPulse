import httpx
import re
from typing import Tuple

class DeadLinkValidator:
    SOFT_404_PATTERNS = [
        r"page not found",
        r"looks like nothing was found",
        r"job not found",
        r"position has been closed",
        r"position has been filled",
        r"no longer accepting applications",
        r"job is no longer available",
        r"opportunity is no longer available",
        r"this posting has expired",
        r"this job has expired",
        r"404 not found",
        r"404 error",
        r"requisition is no longer open",
        r"job has been removed"
    ]

    @classmethod
    async def validate_url_alive(cls, url: str, timeout_seconds: float = 3.5) -> Tuple[bool, int]:
        """
        Async HTTP verification to ensure job URL is live.
        Validates HTTP status code (200/302) and checks for soft 404 / closed posting indicators in HTML.
        Rejects 404, 410, 500, dead links, and soft 404s.
        """
        if not url or url == "#":
            return False, 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
                try:
                    res = await client.get(url)
                except Exception:
                    # Fallback to HEAD if GET times out
                    try:
                        res = await client.head(url)
                    except Exception:
                        return False, 0

                status_code = res.status_code
                if status_code not in [200, 301, 302, 307, 308]:
                    return False, status_code

                # Soft 404 Inspection for status 200 responses
                if status_code == 200 and hasattr(res, 'text') and res.text:
                    body_sample = res.text[:5000].lower() # Inspect first 5KB
                    for pattern in cls.SOFT_404_PATTERNS:
                        if re.search(pattern, body_sample):
                            return False, 404

                return True, status_code

        except Exception:
            return False, 0
