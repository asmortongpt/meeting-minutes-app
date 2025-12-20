"""
Enhanced Meeting Minutes - Database Models
PostgreSQL schema with full-text search, version control, and analytics
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, ARRAY,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, BigInteger, Float, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR, INET
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property


Base = declarative_base()


# ============================================================================
# User & Organization Models
# ============================================================================

class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("UserRole", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class UserRole(Base):
    """Association table for User-Role many-to-many relationship"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="user_roles")
    role = relationship("Role", back_populates="users")

    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
        Index('idx_user_roles_user', 'user_id'),
        Index('idx_user_roles_role', 'role_id'),
    )


class User(Base):
    """User model with OAuth support"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)

    # OAuth
    oauth_provider = Column(String(50), nullable=True)  # microsoft, google, github
    oauth_id = Column(String(255), nullable=True, index=True)

    # Role & Status
    role = Column(String(50), default="user", nullable=False)  # user, admin, superadmin
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Settings
    preferences = Column(JSONB, default={})
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    memberships = relationship("OrganizationMember", back_populates="user", cascade="all, delete-orphan")
    created_meetings = relationship("Meeting", back_populates="creator", foreign_keys="Meeting.created_by")
    action_items_assigned = relationship("ActionItem", back_populates="assignee", foreign_keys="ActionItem.owner_id")
    comments = relationship("MeetingComment", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    @property
    def roles(self):
        """Get user roles"""
        return [ur.role for ur in self.user_roles]

    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_oauth', 'oauth_provider', 'oauth_id'),
    )

    def __repr__(self):
        return f"<User {self.email}>"


class Organization(Base):
    """Organization/Team model"""
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)

    # Settings
    settings = Column(JSONB, default={})
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    subscription_expires_at = Column(DateTime, nullable=True)

    # Limits
    max_members = Column(Integer, default=10)
    max_meetings_per_month = Column(Integer, default=100)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="organization", cascade="all, delete-orphan")
    integration_tokens = relationship("IntegrationToken", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization {self.name}>"


class OrganizationMember(Base):
    """Organization membership with roles"""
    __tablename__ = "organization_members"

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50), default="member", nullable=False)  # owner, admin, member
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


# ============================================================================
# Meeting Models
# ============================================================================

class Meeting(Base):
    """Enhanced meeting model with AI analysis"""
    __tablename__ = "meetings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Basic Info
    project_name = Column(String(255), nullable=False)
    meeting_date = Column(DateTime, nullable=False, index=True)
    meeting_purpose = Column(Text, nullable=True)
    meeting_type = Column(String(50), nullable=True)  # standup, planning, retrospective, client, other

    # Content (JSONB for flexibility)
    agenda_items = Column(JSONB, default=[])
    attendees = Column(JSONB, default=[])
    action_items_json = Column(JSONB, default=[])  # Deprecated - use ActionItem table
    decisions = Column(JSONB, default=[])
    notes = Column(Text, nullable=True)

    # AI Analysis Results
    transcript = Column(Text, nullable=True)
    transcript_segments = Column(JSONB, nullable=True)  # [{speaker, text, timestamp, confidence}]
    speakers = Column(JSONB, nullable=True)  # [{name, role, total_time, sentiment}]
    sentiment_analysis = Column(JSONB, nullable=True)  # {overall, by_speaker, by_topic}
    key_moments = Column(JSONB, nullable=True)  # [{timestamp, description, importance}]
    ai_summary = Column(Text, nullable=True)
    quality_score = Column(Integer, nullable=True)  # 0-100

    # Metadata
    tags = Column(ARRAY(String), default=[])
    category = Column(String(100), nullable=True)
    status = Column(String(50), default="draft", nullable=False)  # draft, published, archived
    duration_minutes = Column(Integer, nullable=True)
    recording_url = Column(Text, nullable=True)

    # Analytics
    view_count = Column(Integer, default=0)
    export_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Full-Text Search (populated via trigger or application logic)
    search_vector = Column(TSVECTOR, nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="meetings")
    creator = relationship("User", back_populates="created_meetings", foreign_keys=[created_by])
    versions = relationship("MeetingVersion", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    comments = relationship("MeetingComment", back_populates="meeting", cascade="all, delete-orphan")
    media_files = relationship("MediaFile", back_populates="meeting", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_meetings_org_date', 'organization_id', 'meeting_date'),
        Index('idx_meetings_search', 'search_vector', postgresql_using='gin'),
        Index('idx_meetings_status', 'status'),
        Index('idx_meetings_type', 'meeting_type'),
        CheckConstraint('quality_score >= 0 AND quality_score <= 100', name='check_quality_score'),
    )

    def __repr__(self):
        return f"<Meeting {self.project_name} on {self.meeting_date}>"


class MeetingVersion(Base):
    """Meeting version history for audit trail"""
    __tablename__ = "meeting_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    data = Column(JSONB, nullable=False)  # Complete meeting state snapshot
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="versions")

    __table_args__ = (
        UniqueConstraint('meeting_id', 'version_number', name='uq_meeting_version'),
        Index('idx_versions_meeting', 'meeting_id', 'version_number'),
    )


class ActionItem(Base):
    """Action items extracted from meetings"""
    __tablename__ = "action_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Assignment
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee_email = Column(String(255), nullable=True)  # For external assignees

    # Scheduling
    due_date = Column(Date, nullable=True, index=True)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, in_progress, completed, cancelled

    # Integration
    external_ticket_id = Column(String(255), nullable=True)
    external_ticket_url = Column(Text, nullable=True)
    external_system = Column(String(50), nullable=True)  # jira, asana, trello, etc.

    # AI Metadata
    confidence_score = Column(Float, nullable=True)  # 0.0-1.0
    extracted_by_ai = Column(Boolean, default=False)

    # Timestamps
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")
    assignee = relationship("User", back_populates="action_items_assigned", foreign_keys=[owner_id])

    __table_args__ = (
        Index('idx_action_items_status_due', 'status', 'due_date'),
        Index('idx_action_items_owner', 'owner_id'),
    )

    @hybrid_property
    def is_overdue(self):
        """Check if action item is overdue"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return self.due_date < datetime.utcnow().date()
        return False


class MeetingComment(Base):
    """Comments on meetings for collaboration"""
    __tablename__ = "meeting_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("meeting_comments.id", ondelete="CASCADE"), nullable=True)
    mentions = Column(ARRAY(UUID(as_uuid=True)), default=[])
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="comments")
    user = relationship("User", back_populates="comments")


# ============================================================================
# Media & Files
# ============================================================================

class MediaFile(Base):
    """Audio/Video/Image files uploaded for meetings"""
    __tablename__ = "media_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)

    # File Info
    file_type = Column(String(50), nullable=False)  # audio, video, image
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)

    # Processing Status
    transcription_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    transcription_job_id = Column(String(255), nullable=True)
    transcription_error = Column(Text, nullable=True)

    # Metadata
    duration_seconds = Column(Integer, nullable=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    meeting = relationship("Meeting", back_populates="media_files")


# ============================================================================
# Integrations
# ============================================================================

class Integration(Base):
    """Integration model for external services"""
    __tablename__ = "integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # calendar, slack, jira, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Integration {self.name}>"


class IntegrationToken(Base):
    """OAuth tokens for third-party integrations"""
    __tablename__ = "integration_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    service = Column(String(50), nullable=False)  # microsoft, google, slack, jira, etc.
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    scopes = Column(ARRAY(String), default=[])
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="integration_tokens")

    __table_args__ = (
        UniqueConstraint('user_id', 'organization_id', 'service', name='uq_integration_token'),
    )


# ============================================================================
# Analytics & Metrics
# ============================================================================

class AnalyticsEvent(Base):
    """Event tracking for analytics"""
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id", ondelete="SET NULL"), nullable=True)
    properties = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index('idx_analytics_type_created', 'event_type', 'created_at'),
        Index('idx_analytics_org_created', 'organization_id', 'created_at'),
    )


class AuditLog(Base):
    """Comprehensive audit logging for compliance"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index('idx_audit_action_created', 'action', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
