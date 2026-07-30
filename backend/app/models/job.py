import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(100), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_job_id = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False, index=True)
    remote_type = Column(String(50), default="Hybrid", index=True) # Remote, Hybrid, On-site
    employment_type = Column(String(50), default="Full-time") # Full-time, Internship, Contract
    experience_level = Column(String(50), nullable=False, default="Fresh Graduate", index=True) # Internship, Fresh Graduate, 0-2 YOE, Mid
    salary_range = Column(String(100), nullable=True) # e.g. "₹10 - ₹14 LPA"
    min_salary_lpa = Column(Float, nullable=True, index=True)
    max_salary_lpa = Column(Float, nullable=True, index=True)
    currency = Column(String(10), default="INR")
    apply_url = Column(Text, nullable=False)
    canonical_url = Column(Text, nullable=True)
    source = Column(String(100), nullable=False, index=True) # e.g. "Greenhouse", "Lever", "Tech Careers"
    source_type = Column(String(50), default="ATS")
    raw_tags = Column(String(255), nullable=True) # Tech keywords e.g. "Python, React, FastAPI"
    description = Column(Text, nullable=True)
    hash_signature = Column(String(64), unique=True, index=True, nullable=False)
    is_bookmarked = Column(Boolean, default=False, index=True)
    posted_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    query = Column(String(255), nullable=True) # e.g. "Backend AND Python"
    keywords = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    min_salary_lpa = Column(Float, nullable=True)
    experience_level = Column(String(50), nullable=True)
    remote_type = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    last_matched = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    folder = Column(String(50), default="Interested") # Interested, Applied, Interview, Offer, Rejected, Archive
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ApplicationTracker(Base):
    __tablename__ = "application_tracker"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    status = Column(String(50), default="Applied") # Interested, Applied, OA, Interview, Offer, Rejected, Accepted
    notes = Column(Text, nullable=True)
    applied_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    saved_search_id = Column(Integer, nullable=True)
    channel = Column(String(50), nullable=False, default="Telegram") # Telegram, Email
    recipient = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="DELIVERED") # QUEUED, DELIVERED, FAILED
    match_reason = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

class ConnectorHealth(Base):
    __tablename__ = "connector_health"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False) # ATS, Custom Scraper
    status = Column(String(50), default="ACTIVE") # ACTIVE, ERROR, DEGRADED, DISABLED
    last_run = Column(DateTime, nullable=True)
    jobs_found_last_run = Column(Integer, default=0)
    total_jobs_indexed = Column(Integer, default=0)
    average_runtime_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
