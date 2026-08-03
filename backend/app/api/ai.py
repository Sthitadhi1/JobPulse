from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.database import get_db
from backend.app.models.job import Job
from backend.app.engine.ai_layer import AIEngineLayer

router = APIRouter(prefix="/ai", tags=["AI Features"])

@router.post("/parse-query")
async def parse_nl_query(payload: dict = Body(...)):
    query = payload.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query string is required.")
    
    parsed = AIEngineLayer.parse_natural_language_query(query)
    return {
        "success": True,
        "query": query,
        "parsed_filters": parsed
    }

@router.post("/match-resume")
async def match_resume(payload: dict = Body(...), db: AsyncSession = Depends(get_db)):
    job_id = payload.get("job_id")
    resume_text = payload.get("resume_text", "")

    if not job_id or not resume_text:
        raise HTTPException(status_code=400, detail="job_id and resume_text are required.")

    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    analysis = AIEngineLayer.match_resume_to_job(resume_text, job)
    return {
        "success": True,
        "data": analysis
    }

@router.post("/recommendations")
async def recommend_jobs(payload: dict = Body(...), db: AsyncSession = Depends(get_db)):
    skills = payload.get("skills", [])
    limit = payload.get("limit", 10)
    
    recs = await AIEngineLayer.get_recommendations(db, skills, limit)
    return {
        "success": True,
        "count": len(recs),
        "data": recs
    }
