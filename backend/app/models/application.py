import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

class JobApplication(Base):
    """
    PART 7 & 8 — Application Workspace & Audit Timeline Schema
    Tracks full job application lifecycle: Saved -> Applied -> OA -> Interview -> Offer / Rejected.
    """
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), default="default_user", index=True)
    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=False, index=True)
    source = Column(String(100), nullable=True) # LinkedIn, Indeed, Company Site
    job_url = Column(Text, nullable=True)
    
    # Lifecycle Status: Saved, Applied, OA Scheduled, Interview, HR Round, Offer, Rejected, Withdrawn
    status = Column(String(50), default="Saved", index=True)
    
    applied_date = Column(DateTime, nullable=True)
    resume_version = Column(String(100), nullable=True) # e.g. "v2_sde_resume.pdf"
    cover_letter_version = Column(String(100), nullable=True)
    recruiter_name = Column(String(150), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    interview_date = Column(DateTime, nullable=True)
    expected_salary = Column(Float, nullable=True)
    offer_salary = Column(Float, nullable=True)
    reminder_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    priority = Column(String(20), default="Medium") # Low, Medium, High
    tags = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    timeline_events = relationship("ApplicationTimeline", back_populates="application", cascade="all, delete-orphan")

class ApplicationTimeline(Base):
    __tablename__ = "application_timeline"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False, index=True)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    application = relationship("JobApplication", back_populates="timeline_events")
