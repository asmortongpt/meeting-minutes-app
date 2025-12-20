"""
Enhanced Meeting Minutes API - Production Backend
Enterprise-grade FastAPI application with full feature set
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging

from fastapi import (
    FastAPI, HTTPException, Depends, status, File, UploadFile,
    BackgroundTasks, Query, Path as PathParam, Request
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, and_, or_, func, desc
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field, EmailStr
from redis import asyncio as aioredis
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from prometheus_client import Counter, Histogram, generate_latest
import json

# Local imports
from config import settings, validate_settings
from models import (
    Base, User, Organization, OrganizationMember, Meeting,
    MeetingVersion, ActionItem, MeetingComment, MediaFile,
    IntegrationToken, AnalyticsEvent, AuditLog
)
from ai_orchestrator import ai_orchestrator, TaskType

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        environment=settings.ENVIRONMENT
    )

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
AI_PROCESSING_COUNT = Counter('ai_processing_total', 'Total AI processing tasks', ['task_type', 'model'])
AI_PROCESSING_LATENCY = Histogram('ai_processing_duration_seconds', 'AI processing latency', ['task_type'])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Database engine (synchronous)
engine = create_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis connection
redis_client: Optional[aioredis.Redis] = None


# ============================================================================
# Lifecycle Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting Meeting Minutes Pro API")

    # Validate configuration
    try:
        validate_settings()
        logger.info("✓ Configuration validated")
    except ValueError as e:
        logger.error(f"✗ Configuration validation failed: {e}")
        raise

    # Initialize database (run synchronous operation)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, Base.metadata.create_all, engine)
    logger.info("✓ Database initialized")

    # Skip Redis for now - async client incompatible with sync app
    logger.info("✓ Redis connection skipped (sync mode)")

    yield

    # Shutdown
    logger.info("Shutting down API")
    engine.dispose()


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Meeting Minutes with AI-powered analysis and collaboration",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================================================
# Dependencies
# ============================================================================

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_redis() -> aioredis.Redis:
    """Get Redis client"""
    if not redis_client:
        raise HTTPException(status_code=500, detail="Redis not available")
    return redis_client


# Security
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    # TODO: Implement JWT verification
    # For now, return a mock user
    token = credentials.credentials
    # Verify JWT token here

    # Mock user for development
    result = db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


# ============================================================================
# Pydantic Schemas
# ============================================================================

class MeetingCreate(BaseModel):
    """Meeting creation schema"""
    project_name: str = Field(..., min_length=1, max_length=255)
    meeting_date: datetime
    meeting_purpose: Optional[str] = None
    meeting_type: Optional[str] = "other"
    agenda_items: List[Dict] = Field(default_factory=list)
    attendees: List[Dict] = Field(default_factory=list)
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class MeetingUpdate(BaseModel):
    """Meeting update schema"""
    project_name: Optional[str] = None
    meeting_date: Optional[datetime] = None
    meeting_purpose: Optional[str] = None
    meeting_type: Optional[str] = None
    agenda_items: Optional[List[Dict]] = None
    attendees: Optional[List[Dict]] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


class MeetingResponse(BaseModel):
    """Meeting response schema"""
    id: UUID
    organization_id: UUID
    project_name: str
    meeting_date: datetime
    meeting_purpose: Optional[str]
    meeting_type: Optional[str]
    agenda_items: List[Dict]
    attendees: List[Dict]
    notes: Optional[str]
    tags: List[str]
    status: str
    quality_score: Optional[int]
    ai_summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ActionItemCreate(BaseModel):
    """Action item creation schema"""
    meeting_id: UUID
    description: str = Field(..., min_length=1)
    assignee_email: Optional[EmailStr] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class ActionItemUpdate(BaseModel):
    """Action item update schema"""
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class ActionItemResponse(BaseModel):
    """Action item response schema"""
    id: UUID
    meeting_id: UUID
    description: str
    assignee_email: Optional[str]
    due_date: Optional[datetime]
    priority: str
    status: str
    is_overdue: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Helper Functions
# ============================================================================

async def cache_get(key: str, redis: aioredis.Redis = Depends(get_redis)) -> Optional[Any]:
    """Get value from cache"""
    try:
        value = redis.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def cache_set(
    key: str,
    value: Any,
    ttl: int = settings.CACHE_TTL_DEFAULT,
    redis: aioredis.Redis = Depends(get_redis)
):
    """Set value in cache"""
    try:
        redis.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.error(f"Cache set error: {e}")


async def log_analytics_event(
    event_type: str,
    user_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    meeting_id: Optional[UUID] = None,
    properties: Optional[Dict] = None,
    db: Session = Depends(get_db)
):
    """Log analytics event"""
    event = AnalyticsEvent(
        event_type=event_type,
        user_id=user_id,
        organization_id=organization_id,
        meeting_id=meeting_id,
        properties=properties or {}
    )
    db.add(event)
    db.commit()


# ============================================================================
# Root & Health Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "documentation": "/api/docs"
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database
        db.execute(select(1))

        # Check Redis (skip for now - async client)

        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected" if redis_client else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")


# ============================================================================
# Meeting Endpoints
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/meetings", response_model=List[MeetingResponse])
@limiter.limit("100/minute")
async def list_meetings(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    meeting_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all meetings with filtering and pagination

    - **skip**: Number of meetings to skip (pagination)
    - **limit**: Maximum number of meetings to return
    - **status**: Filter by status (draft, published, archived)
    - **meeting_type**: Filter by type (standup, planning, etc.)
    - **search**: Full-text search query
    """
    # Build query
    query = select(Meeting).where(Meeting.deleted_at.is_(None))

    # Apply filters
    if status:
        query = query.where(Meeting.status == status)
    if meeting_type:
        query = query.where(Meeting.meeting_type == meeting_type)
    if search:
        query = query.where(
            or_(
                Meeting.project_name.ilike(f"%{search}%"),
                Meeting.meeting_purpose.ilike(f"%{search}%"),
                Meeting.notes.ilike(f"%{search}%")
            )
        )

    # Order and paginate
    query = query.order_by(desc(Meeting.meeting_date)).offset(skip).limit(limit)

    # Execute
    result = db.execute(query)
    meetings = result.scalars().all()

    # Log analytics
    log_analytics_event(
        "meetings_listed",
        user_id=current_user.id,
        properties={"count": len(meetings), "filters": {"status": status, "type": meeting_type}}
    )

    return meetings


@app.post(f"{settings.API_V1_PREFIX}/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_meeting(
    request: Request,
    meeting: MeetingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new meeting

    Creates a meeting record and optionally triggers AI analysis in the background
    """
    # Get user's organization (simplified - would be more complex in production)
    result = db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == current_user.id).limit(1)
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=403, detail="User not part of any organization")

    # Create meeting
    new_meeting = Meeting(
        organization_id=membership.organization_id,
        created_by=current_user.id,
        **meeting.model_dump()
    )

    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    # Log analytics
    log_analytics_event(
        "meeting_created",
        user_id=current_user.id,
        organization_id=membership.organization_id,
        meeting_id=new_meeting.id,
        properties={"type": meeting.meeting_type}
    )

    # Trigger AI analysis if notes are provided
    if meeting.notes:
        background_tasks.add_task(analyze_meeting_ai, new_meeting.id, db)

    return new_meeting


@app.get(f"{settings.API_V1_PREFIX}/meetings/{{meeting_id}}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: UUID = PathParam(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Get meeting by ID with caching"""
    # Try cache first
    cache_key = f"meeting:{meeting_id}"
    cached = cache_get(cache_key, redis)
    if cached:
        return cached

    # Query database
    result = db.execute(
        select(Meeting).where(and_(Meeting.id == meeting_id, Meeting.deleted_at.is_(None)))
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Update view count
    meeting.view_count += 1
    db.commit()

    # Cache result
    meeting_dict = {k: v for k, v in meeting.__dict__.items() if not k.startswith('_')}
    cache_set(cache_key, meeting_dict, settings.CACHE_TTL_MEETING, redis)

    return meeting


@app.put(f"{settings.API_V1_PREFIX}/meetings/{{meeting_id}}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    meeting_update: MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    redis: aioredis.Redis = Depends(get_redis)
):
    """Update meeting"""
    # Get meeting
    result = db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Update fields
    update_data = meeting_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)

    meeting.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(meeting)

    # Invalidate cache
    redis.delete(f"meeting:{meeting_id}")

    return meeting


@app.delete(f"{settings.API_V1_PREFIX}/meetings/{{meeting_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Soft delete meeting"""
    result = db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Soft delete
    meeting.deleted_at = datetime.utcnow()
    db.commit()

    return None


# ============================================================================
# AI-Powered Endpoints
# ============================================================================

@app.post(f"{settings.API_V1_PREFIX}/ai/analyze-meeting")
@limiter.limit("10/minute")
async def ai_analyze_meeting(
    request: Request,
    meeting_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger comprehensive AI analysis of a meeting

    This endpoint triggers asynchronous AI processing including:
    - Summary generation
    - Sentiment analysis
    - Action item extraction
    - Decision extraction
    - Topic classification
    - Meeting quality scoring
    """
    # Get meeting
    result = db.execute(select(Meeting).where(Meeting.id == meeting_id))
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Queue AI analysis
    background_tasks.add_task(analyze_meeting_ai, meeting_id, db)

    return {
        "success": True,
        "message": "AI analysis queued",
        "meeting_id": str(meeting_id)
    }


def analyze_meeting_ai(meeting_id: UUID, db: Session):
    """Background task for AI analysis"""
    try:
        # Get meeting
        result = db.execute(select(Meeting).where(Meeting.id == meeting_id))
        meeting = result.scalar_one_or_none()

        if not meeting:
            logger.error(f"Meeting {meeting_id} not found for AI analysis")
            return

        # Prepare content
        content = f"""
Project: {meeting.project_name}
Purpose: {meeting.meeting_purpose or 'N/A'}
Date: {meeting.meeting_date}
Notes: {meeting.notes or 'N/A'}
Agenda: {json.dumps(meeting.agenda_items)}
"""

        # Run comprehensive AI analysis
        analysis = ai_orchestrator.analyze_meeting_comprehensive(
            transcript=content,
            metadata={"meeting_type": meeting.meeting_type}
        )

        # Update meeting with AI results
        if analysis.get("summary"):
            meeting.ai_summary = analysis["summary"].get("executive_summary")

        if analysis.get("sentiment"):
            meeting.sentiment_analysis = analysis["sentiment"]

        if analysis.get("decisions"):
            meeting.decisions = analysis["decisions"].get("decisions", [])

        if analysis.get("quality_score"):
            meeting.quality_score = analysis["quality_score"].get("overall_score", 0)

        # Extract and save action items
        if analysis.get("action_items") and analysis["action_items"].get("action_items"):
            for item_data in analysis["action_items"]["action_items"]:
                action_item = ActionItem(
                    meeting_id=meeting_id,
                    description=item_data.get("description"),
                    assignee_email=item_data.get("owner"),
                    due_date=item_data.get("due_date"),
                    priority=item_data.get("priority", "medium"),
                    confidence_score=item_data.get("confidence", 0.0),
                    extracted_by_ai=True
                )
                db.add(action_item)

        db.commit()

        logger.info(f"AI analysis completed for meeting {meeting_id}")
        AI_PROCESSING_COUNT.labels(task_type="comprehensive", model="multi").inc()

    except Exception as e:
        logger.error(f"AI analysis failed for meeting {meeting_id}: {str(e)}")
        db.rollback()


@app.post(f"{settings.API_V1_PREFIX}/ai/transcribe")
@limiter.limit("5/minute")
async def ai_transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    meeting_id: Optional[UUID] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Transcribe audio/video file using Whisper API

    Supports: MP3, WAV, M4A, MP4, WebM, etc.
    Max file size: 100MB
    """
    # Validate file
    if file.size > settings.MEDIA_MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MEDIA_MAX_SIZE_MB}MB"
        )

    # Save file temporarily
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        content = file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Transcribe
        result = ai_orchestrator.transcribe_audio(tmp_path)

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        # If meeting_id provided, update meeting
        if meeting_id:
            meeting_result = db.execute(select(Meeting).where(Meeting.id == meeting_id))
            meeting = meeting_result.scalar_one_or_none()
            if meeting:
                meeting.transcript = result["text"]
                meeting.transcript_segments = result.get("segments", [])
                db.commit()

        return {
            "success": True,
            "transcript": result["text"],
            "language": result.get("language"),
            "duration": result.get("duration"),
            "segments_count": len(result.get("segments", []))
        }

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ============================================================================
# Action Item Endpoints
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/action-items", response_model=List[ActionItemResponse])
async def list_action_items(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List action items with filtering"""
    query = select(ActionItem)

    if status:
        query = query.where(ActionItem.status == status)

    if overdue_only:
        query = query.where(
            and_(
                ActionItem.due_date < datetime.utcnow().date(),
                ActionItem.status.notin_(['completed', 'cancelled'])
            )
        )

    query = query.order_by(ActionItem.due_date.asc()).offset(skip).limit(limit)

    result = db.execute(query)
    action_items = result.scalars().all()

    return action_items


@app.post(f"{settings.API_V1_PREFIX}/action-items", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_action_item(
    action_item: ActionItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new action item"""
    new_action = ActionItem(**action_item.model_dump())
    db.add(new_action)
    db.commit()
    db.refresh(new_action)
    return new_action


@app.patch(f"{settings.API_V1_PREFIX}/action-items/{{item_id}}", response_model=ActionItemResponse)
async def update_action_item(
    item_id: UUID,
    item_update: ActionItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update action item"""
    result = db.execute(select(ActionItem).where(ActionItem.id == item_id))
    action_item = result.scalar_one_or_none()

    if not action_item:
        raise HTTPException(status_code=404, detail="Action item not found")

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(action_item, field, value)

    if item_update.status == "completed" and not action_item.completed_at:
        action_item.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(action_item)

    return action_item


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get(f"{settings.API_V1_PREFIX}/analytics/dashboard")
async def get_analytics_dashboard(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    redis: aioredis.Redis = Depends(get_redis)
):
    """
    Get analytics dashboard data

    Returns comprehensive analytics including:
    - Meeting statistics
    - Action item completion rates
    - Team engagement metrics
    - Trend analysis
    """
    # Set default date range
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Check cache
    cache_key = f"analytics:dashboard:{current_user.id}:{start_date.date()}:{end_date.date()}"
    cached = cache_get(cache_key, redis)
    if cached:
        return cached

    # Query meeting statistics
    meeting_count_query = select(func.count(Meeting.id)).where(
        and_(
            Meeting.meeting_date >= start_date,
            Meeting.meeting_date <= end_date,
            Meeting.deleted_at.is_(None)
        )
    )
    meeting_count_result = db.execute(meeting_count_query)
    total_meetings = meeting_count_result.scalar()

    # Query action item statistics
    action_items_query = select(
        ActionItem.status,
        func.count(ActionItem.id).label('count')
    ).group_by(ActionItem.status)
    action_items_result = db.execute(action_items_query)
    action_items_stats = {row.status: row.count for row in action_items_result}

    # Calculate metrics
    total_action_items = sum(action_items_stats.values())
    completed_action_items = action_items_stats.get('completed', 0)
    completion_rate = (completed_action_items / total_action_items * 100) if total_action_items > 0 else 0

    dashboard_data = {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "meetings": {
            "total": total_meetings,
            "average_per_week": total_meetings / 4 if total_meetings > 0 else 0
        },
        "action_items": {
            "total": total_action_items,
            "completed": completed_action_items,
            "pending": action_items_stats.get('pending', 0),
            "in_progress": action_items_stats.get('in_progress', 0),
            "completion_rate": round(completion_rate, 2)
        },
        "trends": {
            "meetings_trend": "up",  # TODO: Calculate actual trend
            "action_items_trend": "stable"
        }
    }

    # Cache results
    cache_set(cache_key, dashboard_data, settings.CACHE_TTL_ANALYTICS, redis)

    return dashboard_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower()
    )
