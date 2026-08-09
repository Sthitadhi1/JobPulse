import httpx
from typing import Tuple

class DeadLinkValidator:
    @classmethod
    async def validate_url_alive(cls, url: str, timeout_seconds: float = 2.5) -> Tuple[bool, int]:
        """
        PART 3 — Dead Link Fix:
        Performs async HTTP HEAD request (with GET fallback if 405) to ensure job URL is live.
        Only accepts HTTP 200 or 302.
        Rejects 404, 410, 500, and redirect loops.
        """
        if not url or url == "#":
            return False, 0

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
                try:
                    res = await client.head(url)
                except Exception:
                    res = None

                if res is None or res.status_code == 405:
                    res = await client.get(url)

                status_code = res.status_code
                if status_code in [200, 302]:
                    return True, status_code

                return False, status_code

        except Exception:
            return False, 0
