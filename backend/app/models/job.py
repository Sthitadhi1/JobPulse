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
    telegram_connected = Column(Boolean, default=False)
    telegram_token = Column(String(100), nullable=True, index=True)
    last_notification_sent = Column(DateTime, nullable=True)
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
    experience_level = Column(String(50), nullable=False, default="Fresher / 0-1 YOE", index=True)
    salary_range = Column(String(100), nullable=True) # e.g. "₹10 - ₹14 LPA"
    min_salary_lpa = Column(Float, nullable=True, index=True)
    max_salary_lpa = Column(Float, nullable=True, index=True)
    currency = Column(String(10), default="INR")
    
    # URL Normalization
    job_url = Column(Text, nullable=False) # URL of individual job listing
    source_url = Column(Text, nullable=False) # URL of career page / board listing
    external_apply_url = Column(Text, nullable=True) # Optional direct employer apply URL
    apply_url = Column(Text, nullable=True) # Backward compatibility
    canonical_url = Column(Text, nullable=True)

    source = Column(String(100), nullable=False, index=True) # e.g. "Greenhouse", "Lever", "LinkedIn Jobs", "Naukri India"
    source_type = Column(String(50), default="ATS") # ATS, Job Board, Company
    raw_tags = Column(String(255), nullable=True) # Tech keywords e.g. "Python, React, FastAPI"
    description = Column(Text, nullable=True)
    hash_signature = Column(String(64), unique=True, index=True, nullable=False)
    is_bookmarked = Column(Boolean, default=False, index=True)
    posted_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=False)
    query = Column(String(255), nullable=True)
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
    folder = Column(String(50), default="Interested")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ApplicationTracker(Base):
    __tablename__ = "application_tracker"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    status = Column(String(50), default="Applied")
    notes = Column(Text, nullable=True)
    applied_date = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    saved_search_id = Column(Integer, nullable=True)
    channel = Column(String(50), nullable=False, default="Telegram")
    recipient = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="DELIVERED")
    match_reason = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)

class ConnectorHealth(Base):
    __tablename__ = "connector_health"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)
    status = Column(String(50), default="ACTIVE")
    last_run = Column(DateTime, nullable=True)
    jobs_found_last_run = Column(Integer, default=0)
    total_jobs_indexed = Column(Integer, default=0)
    average_runtime_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)

class ConnectorExecution(Base):
    __tablename__ = "connector_executions"

    id = Column(Integer, primary_key=True, index=True)
    connector_name = Column(String(100), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, default="Company")
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    duration_ms = Column(Float, nullable=False, default=0.0)
    jobs_discovered = Column(Integer, default=0)
    jobs_inserted = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    jobs_skipped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    status = Column(String(50), default="SUCCESS", index=True)
