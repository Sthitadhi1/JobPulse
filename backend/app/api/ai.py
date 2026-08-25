import json
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Body, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.database import get_db
from backend.app.models.job import Job, CandidateProfile, User
from backend.app.api.auth import get_current_user_optional
from backend.app.engine.ai_layer import AIEngineLayer
from backend.app.engine.resume_parser import ResumeParserEngine

router = APIRouter(prefix="/ai", tags=["AI Features"])

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 # 10 MB

@router.post("/upload-resume")
async def upload_and_parse_resume(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    PART 4 & 5 & 6 — Resume Upload, Parsing & Top 30 Recommendations.
    Supports PDF and DOCX uploads up to 10 MB.
    Parses candidate profile and generates top 30 active job recommendations.
    """
    extracted_text = ""
    filename = "resume.pdf"

    if file:
        filename = file.filename or "resume.pdf"
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext not in ["pdf", "docx", "doc", "txt"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format .{ext}. Please upload a PDF or DOCX file."
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="File size exceeds maximum limit of 10 MB."
            )

        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty or corrupted."
            )

        extracted_text = ResumeParserEngine.extract_text(content, filename)

    if not extracted_text and resume_text:
        extracted_text = resume_text.strip()

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract readable text from document. Please ensure the document is a valid PDF or DOCX file."
        )

    # Parse profile
    parsed_profile = ResumeParserEngine.parse_profile(extracted_text, filename)

    # Save to user profile in DB if user is authenticated
    if current_user:
        res = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
        cp = res.scalars().first()
        if cp:
            cp.resume_filename = filename
            cp.resume_text = extracted_text
            cp.parsed_json = json.dumps(parsed_profile)
            cp.skills = ", ".join(parsed_profile.get("skills", []))
            cp.experience_level = parsed_profile.get("experience_level")
            cp.preferred_roles = ", ".join(parsed_profile.get("preferred_roles", []))
        else:
            cp = CandidateProfile(
                user_id=current_user.id,
                resume_filename=filename,
                resume_text=extracted_text,
                parsed_json=json.dumps(parsed_profile),
                skills=", ".join(parsed_profile.get("skills", [])),
                experience_level=parsed_profile.get("experience_level"),
                preferred_roles=", ".join(parsed_profile.get("preferred_roles", []))
            )
            db.add(cp)
        await db.commit()

    # Generate Top 30 Recommendations against Job.status == "ACTIVE"
    recommendations = await AIEngineLayer.get_top_30_recommendations(db, parsed_profile)

    return {
        "success": True,
        "message": f"Resume analyzed successfully. Found {len(recommendations)} top active opportunities.",
        "candidate_profile": parsed_profile,
        "total_recommendations": len(recommendations),
        "data": recommendations
    }


@router.get("/recommendations")
async def get_stored_recommendations(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """Returns top 30 recommendations for current user or default candidate profile."""
    candidate_profile = None

    if current_user:
        res = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
        cp = res.scalars().first()
        if cp and cp.parsed_json:
            try:
                candidate_profile = json.loads(cp.parsed_json)
            except Exception:
                candidate_profile = None

    if not candidate_profile:
        # Default student candidate profile
        candidate_profile = {
            "name": current_user.name if current_user else "Student Candidate",
            "degree": "B.Tech / Bachelor's in CS/Tech",
            "experience_level": "Fresher",
            "skills": ["Python", "Java", "React", "FastAPI", "SQL", "Data Structures", "Git", "REST API", "Machine Learning"],
            "preferred_roles": ["Software Development Engineer (SDE 1)", "Backend Engineer", "Full Stack Developer"]
        }

    recommendations = await AIEngineLayer.get_top_30_recommendations(db, candidate_profile)

    return {
        "success": True,
        "candidate_profile": candidate_profile,
        "total_recommendations": len(recommendations),
        "data": recommendations
    }


@router.post("/match-resume")
async def match_resume_to_specific_job(
    payload: dict = Body(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    job_id = payload.get("job_id")
    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required.")

    res = await db.execute(select(Job).where(Job.id == job_id))
    job = res.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    resume_text = payload.get("resume_text", "")
    if resume_text:
        cand_profile = ResumeParserEngine.parse_profile(resume_text)
    elif current_user:
        res_cp = await db.execute(select(CandidateProfile).where(CandidateProfile.user_id == current_user.id))
        cp = res_cp.scalars().first()
        if cp and cp.parsed_json:
            cand_profile = json.loads(cp.parsed_json)
        else:
            cand_profile = {
                "name": current_user.name,
                "skills": ["Python", "React", "SQL", "FastAPI"],
                "experience_level": "Fresher"
            }
    else:
        cand_profile = {
            "name": "Candidate",
            "skills": ["Python", "React", "SQL", "FastAPI"],
            "experience_level": "Fresher"
        }

    match_result = AIEngineLayer.match_candidate_to_job(cand_profile, job)

    return {
        "success": True,
        "data": match_result
    }
