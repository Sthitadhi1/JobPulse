import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Index
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
    is_active = Column(Boolean, default=True, index=True)
    email_verified = Column(Boolean, default=False, index=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class CompanyRegistry(Base):
    __tablename__ = "company_registry"

    id = Column(String(100), primary_key=True, index=True) # e.g. "google", "flipkart"
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), default="Product Company", index=True)
    careers_url = Column(Text, nullable=False)
    ats_provider = Column(String(100), default="Custom", index=True)
    country = Column(String(100), default="India", index=True)
    priority = Column(Integer, default=5, index=True) # 1-5
    crawl_interval = Column(Integer, default=60) # minutes
    enabled = Column(Boolean, default=True, index=True)
    supported_locations = Column(Text, nullable=True)
    supported_roles = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_job_id = Column(String(100), nullable=True, index=True) # Step 18 Index
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True) # Step 18 Index
    department = Column(String(150), nullable=True, index=True)
    location = Column(String(255), nullable=False, index=True) # Step 18 Index
    country = Column(String(100), default="India", index=True)
    remote_type = Column(String(50), default="Hybrid", index=True) # Remote, Hybrid, On-site
    employment_type = Column(String(50), default="Full-time") # Full-time, Internship, Contract
    experience_level = Column(String(50), nullable=False, default="Fresher", index=True) # Step 18 Index
    salary_range = Column(String(100), nullable=True) # e.g. "₹10 - ₹14 LPA"
    min_salary_lpa = Column(Float, nullable=True, index=True)
    max_salary_lpa = Column(Float, nullable=True, index=True)
    currency = Column(String(10), default="INR")
    
    # URL Normalization & Indexing (Step 18)
    job_url = Column(Text, nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    external_apply_url = Column(Text, nullable=True)
    apply_url = Column(Text, nullable=True)
    canonical_url = Column(Text, nullable=True)

    source = Column(String(100), nullable=False, index=True) # Step 18 Index
    source_type = Column(String(50), default="ATS", index=True)
    raw_tags = Column(String(255), nullable=True)
    skills = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    hash_signature = Column(String(64), unique=True, index=True, nullable=False)
    is_bookmarked = Column(Boolean, default=False, index=True)

    # Step 10: Persistent Job Tracking & Verification
    status = Column(String(50), default="ACTIVE", index=True) # ACTIVE, EXPIRED, FILLED, REMOVED, UNKNOWN
    verification_status = Column(String(50), default="VERIFIED", index=True) # Step 18 Index: VERIFIED, PENDING, REMOVED_FROM_SOURCE, FAILED
    first_seen = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    last_verified = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    verification_count = Column(Integer, default=1)
    consecutive_missing_count = Column(Integer, default=0)

    posted_at = Column(DateTime, default=datetime.datetime.utcnow, index=True) # Step 18 Index
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

# Compound Index for high-performance filter queries
Index('idx_jobs_company_exp_status', Job.company, Job.experience_level, Job.status)
Index('idx_jobs_verification_status', Job.verification_status, Job.status)

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
    jobs_verified = Column(Integer, default=0)
    jobs_removed = Column(Integer, default=0)
    average_runtime_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)

class ConnectorExecution(Base):
    __tablename__ = "connector_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(String(36), nullable=True, index=True)
    connector_name = Column(String(100), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, default="Company")
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    duration_ms = Column(Float, nullable=False, default=0.0)
    jobs_discovered = Column(Integer, default=0)
    jobs_inserted = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    jobs_verified = Column(Integer, default=0)
    jobs_removed = Column(Integer, default=0)
    jobs_skipped = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    status = Column(String(50), default="SUCCESS", index=True)

class DiscoveryLock(Base):
    __tablename__ = "discovery_locks"

    id = Column(Integer, primary_key=True, index=True)
    lock_name = Column(String(50), unique=True, index=True, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    execution_id = Column(String(36), nullable=True)
    locked_at = Column(DateTime, nullable=True)

