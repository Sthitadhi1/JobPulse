from typing import Any, Dict, Iterable, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.job import Bookmark, User


async def bookmarked_job_ids(db: AsyncSession, user: Optional[User], job_ids: Iterable[int]) -> Set[int]:
    """Returns the subset of job_ids that the given user has bookmarked (empty when anonymous)."""
    ids = {jid for jid in job_ids if isinstance(jid, int)}
    if not user or not ids:
        return set()
    res = await db.execute(
        select(Bookmark.job_id).where(Bookmark.user_id == user.id, Bookmark.job_id.in_(ids))
    )
    return set(res.scalars().all())


async def annotate_bookmarks(
    db: AsyncSession, user: Optional[User], jobs: List[Dict[str, Any]], id_key: str = "id"
) -> List[Dict[str, Any]]:
    """Sets each job dict's is_bookmarked flag from the signed-in user's own bookmarks."""
    marked = await bookmarked_job_ids(db, user, (j.get(id_key) for j in jobs))
    for j in jobs:
        j["is_bookmarked"] = j.get(id_key) in marked
    return jobs
