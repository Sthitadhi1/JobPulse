from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from backend.app.database import get_db
from backend.app.models.job import SavedSearch, User
from backend.app.api.auth import get_current_user_optional

router = APIRouter(prefix="/search/saved", tags=["Saved Searches"])

class SavedSearchCreate(BaseModel):
    name: str
    query: Optional[str] = None
    keywords: Optional[str] = None
    location: Optional[str] = None
    min_salary_lpa: Optional[float] = None
    experience_level: Optional[str] = None
    remote_type: Optional[str] = None
    telegram_chat_id: Optional[str] = None

@router.get("")
async def list_saved_searches(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SavedSearch)
    if current_user:
        stmt = stmt.where(SavedSearch.user_id == current_user.id)
    else:
        stmt = stmt.where(SavedSearch.user_id == None)
    stmt = stmt.order_by(SavedSearch.id.desc())

    res = await db.execute(stmt)
    searches = res.scalars().all()
    
    return {
        "success": True,
        "message": "Saved searches retrieved.",
        "data": [
            {
                "id": s.id,
                "user_id": s.user_id,
                "name": s.name,
                "query": s.query,
                "keywords": s.keywords,
                "location": s.location,
                "min_salary_lpa": s.min_salary_lpa,
                "experience_level": s.experience_level,
                "remote_type": s.remote_type,
                "telegram_chat_id": s.telegram_chat_id,
                "is_active": s.is_active,
                "last_matched": s.last_matched.isoformat() if s.last_matched else None,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in searches
        ]
    }

@router.post("")
async def create_saved_search(
    body: SavedSearchCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.id if current_user else None
    search_obj = SavedSearch(
        user_id=user_id,
        name=body.name,
        query=body.query,
        keywords=body.keywords or body.query,
        location=body.location,
        min_salary_lpa=body.min_salary_lpa,
        experience_level=body.experience_level,
        remote_type=body.remote_type,
        telegram_chat_id=body.telegram_chat_id or (current_user.telegram_chat_id if current_user else None) or "STUDENT_TELEGRAM_DEMO",
        is_active=True
    )
    db.add(search_obj)
    await db.commit()
    await db.refresh(search_obj)

    return {
        "success": True,
        "message": "Saved search created.",
        "data": {
            "id": search_obj.id,
            "user_id": search_obj.user_id,
            "name": search_obj.name,
            "query": search_obj.query,
            "is_active": search_obj.is_active
        }
    }

@router.patch("/{search_id}/toggle")
async def toggle_saved_search(
    search_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(SavedSearch).where(SavedSearch.id == search_id))
    search_obj = res.scalars().first()
    if not search_obj:
        raise HTTPException(status_code=404, detail="Saved search not found.")

    if search_obj.user_id:
        if not current_user or search_obj.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden. You do not own this saved search.")

    search_obj.is_active = not search_obj.is_active
    await db.commit()

    return {
        "success": True,
        "message": f"Saved search {'activated' if search_obj.is_active else 'paused'}.",
        "data": {"id": search_obj.id, "is_active": search_obj.is_active}
    }

@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(SavedSearch).where(SavedSearch.id == search_id))
    search_obj = res.scalars().first()
    if not search_obj:
        raise HTTPException(status_code=404, detail="Saved search not found.")

    if search_obj.user_id:
        if not current_user or search_obj.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden. You do not own this saved search.")

    await db.delete(search_obj)
    await db.commit()

    return {
        "success": True,
        "message": "Saved search deleted.",
        "data": {"id": search_id}
    }


