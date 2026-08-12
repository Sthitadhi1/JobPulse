import csv
import io
import json
import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.application import JobApplication, ApplicationTimeline
from backend.app.models.job import User
from backend.app.api.auth import get_current_user_optional

router = APIRouter(prefix="/applications", tags=["Applications Workspace"])

@router.get("")
async def list_applications(
    status: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(JobApplication)
    if current_user:
        stmt = stmt.where((JobApplication.user_id == current_user.id) | (JobApplication.user_id == "default_user"))
    if status:
        stmt = stmt.where(JobApplication.status == status)
    stmt = stmt.order_by(JobApplication.updated_at.desc())

    res = await db.execute(stmt)
    apps = res.scalars().all()


    output = []
    for a in apps:
        events_res = await db.execute(
            select(ApplicationTimeline).where(ApplicationTimeline.application_id == a.id).order_by(ApplicationTimeline.timestamp.asc())
        )
        events = events_res.scalars().all()

        output.append({
            "id": a.id,
            "company": a.company,
            "role": a.role,
            "source": a.source,
            "job_url": a.job_url,
            "status": a.status,
            "applied_date": a.applied_date.isoformat() if a.applied_date else None,
            "resume_version": a.resume_version,
            "cover_letter_version": a.cover_letter_version,
            "recruiter_name": a.recruiter_name,
            "recruiter_email": a.recruiter_email,
            "interview_date": a.interview_date.isoformat() if a.interview_date else None,
            "expected_salary": a.expected_salary,
            "offer_salary": a.offer_salary,
            "reminder_date": a.reminder_date.isoformat() if a.reminder_date else None,
            "notes": a.notes,
            "priority": a.priority,
            "tags": a.tags,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "timeline": [
                {
                    "from_status": e.from_status,
                    "to_status": e.to_status,
                    "notes": e.notes,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None
                }
                for e in events
            ]
        })

    return {"success": True, "data": output}

@router.post("")
async def create_application(
    data: dict,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    company = data.get("company")
    role = data.get("role")
    if not company or not role:
        raise HTTPException(status_code=400, detail="Company and Role are required.")

    user_id = current_user.id if current_user else "default_user"

    app = JobApplication(
        user_id=user_id,
        company=company,
        role=role,
        source=data.get("source", "Manual"),
        job_url=data.get("job_url"),
        status=data.get("status", "Saved"),
        applied_date=datetime.datetime.utcnow() if data.get("status") == "Applied" else None,
        resume_version=data.get("resume_version"),
        cover_letter_version=data.get("cover_letter_version"),
        recruiter_name=data.get("recruiter_name"),
        recruiter_email=data.get("recruiter_email"),
        notes=data.get("notes"),
        priority=data.get("priority", "Medium"),
        tags=data.get("tags")
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)

    # Log initial timeline event
    event = ApplicationTimeline(
        application_id=app.id,
        from_status=None,
        to_status=app.status,
        notes="Application created in workspace."
    )
    db.add(event)
    await db.commit()

    return {"success": True, "message": "Application tracked in workspace.", "id": app.id}

@router.patch("/{app_id}")
async def update_application(
    app_id: int,
    data: dict,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = res.scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app.user_id and app.user_id != "default_user":
        if not current_user or app.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden. You do not own this application record.")

    old_status = app.status
    new_status = data.get("status", old_status)

    if "status" in data: app.status = new_status
    if "company" in data: app.company = data["company"]
    if "role" in data: app.role = data["role"]
    if "notes" in data: app.notes = data["notes"]
    if "priority" in data: app.priority = data["priority"]
    if "recruiter_name" in data: app.recruiter_name = data["recruiter_name"]
    if "recruiter_email" in data: app.recruiter_email = data["recruiter_email"]

    app.updated_at = datetime.datetime.utcnow()

    # Log status change to timeline
    if old_status != new_status:
        if new_status == "Applied" and not app.applied_date:
            app.applied_date = datetime.datetime.utcnow()

        event = ApplicationTimeline(
            application_id=app.id,
            from_status=old_status,
            to_status=new_status,
            notes=data.get("timeline_notes", f"Status updated to {new_status}")
        )
        db.add(event)

    await db.commit()
    return {"success": True, "message": f"Application updated to {new_status}"}

@router.delete("/{app_id}")
async def delete_application(
    app_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(JobApplication).where(JobApplication.id == app_id))
    app = res.scalars().first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if app.user_id and app.user_id != "default_user":
        if not current_user or app.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden. You do not own this application record.")

    await db.delete(app)
    await db.commit()

    return {"success": True, "message": "Application deleted."}

@router.post("/import")
async def import_applications_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    PART 9 — CSV / Excel Application Importer
    Automatically maps CSV columns (Company, Role, Status, Applied Date, Notes).
    Ignores duplicates.
    """
    contents = await file.read()
    decoded = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))

    imported_count = 0
    skipped_count = 0

    for row in reader:
        company = row.get("Company") or row.get("company") or row.get("Organization")
        role = row.get("Role") or row.get("role") or row.get("Title") or row.get("Job Title")
        status = row.get("Status") or row.get("status") or "Saved"

        if not company or not role:
            skipped_count += 1
            continue

        # Check duplicate
        dup_res = await db.execute(
            select(JobApplication).where(
                JobApplication.company.ilike(company.strip()),
                JobApplication.role.ilike(role.strip())
            )
        )
        if dup_res.scalars().first():
            skipped_count += 1
            continue

        app = JobApplication(
            company=company.strip(),
            role=role.strip(),
            source=row.get("Source", "CSV Import"),
            job_url=row.get("URL") or row.get("job_url"),
            status=status.strip(),
            notes=row.get("Notes") or row.get("notes")
        )
        db.add(app)
        imported_count += 1

    await db.commit()
    return {
        "success": True,
        "message": f"Successfully imported {imported_count} applications ({skipped_count} duplicates skipped).",
        "imported_count": imported_count,
        "skipped_count": skipped_count
    }

@router.get("/export")
async def export_applications(
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    PART 10 — Application Exporter (CSV / JSON)
    """
    res = await db.execute(select(JobApplication).order_by(JobApplication.id.asc()))
    apps = res.scalars().all()

    if format == "json":
        data = [
            {
                "id": a.id,
                "company": a.company,
                "role": a.role,
                "source": a.source,
                "status": a.status,
                "applied_date": a.applied_date.isoformat() if a.applied_date else None,
                "notes": a.notes
            }
            for a in apps
        ]
        return {"success": True, "data": data}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Company", "Role", "Source", "Status", "Applied Date", "Job URL", "Notes"])

    for a in apps:
        writer.writerow([
            a.company,
            a.role,
            a.source or "Manual",
            a.status,
            a.applied_date.strftime("%Y-%m-%d") if a.applied_date else "",
            a.job_url or "",
            a.notes or ""
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jobpulse_applications_export.csv"}
    )
