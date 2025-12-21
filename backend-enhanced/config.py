"""
Enhanced Meeting Minutes - Configuration Management
Production-grade settings with environment variable support
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, RedisDsn, validator


class Settings(BaseSettings):
    """Application settings with validation"""

    # ============================================================================
    # Application
    # ============================================================================
    APP_NAME: str = "Meeting Minutes Pro"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    API_V1_PREFIX: str = "/api/v1"

    # ============================================================================
    # Server
    # ============================================================================
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    RELOAD: bool = Field(default=False, env="RELOAD")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "https://proud-bay-0fdc8040f.3.azurestaticapps.net"
        ],
        env="CORS_ORIGINS"
    )
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    # ============================================================================
    # Database (PostgreSQL)
    # ============================================================================
    POSTGRES_SERVER: str = Field(default="postgres", env="POSTGRES_SERVER")
    POSTGRES_USER: str = Field(default="meeting_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="SecureMeetingPass2024!", env="POSTGRES_PASSWORD")
    POSTGRES_DB: str = Field(default="meeting_minutes_pro", env="POSTGRES_DB")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")

    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Database Pool Settings
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    DB_POOL_RECYCLE: int = Field(default=3600, env="DB_POOL_RECYCLE")

    # ============================================================================
    # Redis
    # ============================================================================
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_SSL: bool = Field(default=False, env="REDIS_SSL")

    REDIS_URL: Optional[RedisDsn] = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v

        scheme = "rediss" if values.get("REDIS_SSL") else "redis"
        password = values.get("REDIS_PASSWORD")
        auth = f":{password}@" if password else ""

        return f"{scheme}://{auth}{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"

    # Cache TTL (seconds)
    CACHE_TTL_DEFAULT: int = Field(default=3600, env="CACHE_TTL_DEFAULT")
    CACHE_TTL_MEETING: int = Field(default=3600, env="CACHE_TTL_MEETING")
    CACHE_TTL_USER: int = Field(default=7200, env="CACHE_TTL_USER")
    CACHE_TTL_ANALYTICS: int = Field(default=1800, env="CACHE_TTL_ANALYTICS")

    # ============================================================================
    # Celery (Background Jobs)
    # ============================================================================
    CELERY_BROKER_URL: str = Field(default="redis://:RedisSecure2024!@redis:6379/1", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://:RedisSecure2024!@redis:6379/2", env="CELERY_RESULT_BACKEND")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 600  # 10 minutes

    # ============================================================================
    # Security & Authentication
    # ============================================================================
    SECRET_KEY: str = Field(default="phase1-secret-key-change-in-production-min-32-chars-long", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Hashing
    PWD_CONTEXT_SCHEMES: List[str] = ["bcrypt"]
    PWD_BCRYPT_ROUNDS: int = 12

    # OAuth2
    OAUTH_MICROSOFT_CLIENT_ID: Optional[str] = Field(default=None, env="AZURE_CLIENT_ID")
    OAUTH_MICROSOFT_CLIENT_SECRET: Optional[str] = Field(default=None, env="AZURE_CLIENT_SECRET")
    OAUTH_MICROSOFT_TENANT_ID: Optional[str] = Field(default=None, env="AZURE_TENANT_ID")

    OAUTH_GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    OAUTH_GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")

    # ============================================================================
    # AI Services
    # ============================================================================
    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    CLAUDE_MODEL_PRIMARY: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MODEL_FAST: str = "claude-3-haiku-20240307"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL_PRIMARY: str = "gpt-4-turbo-preview"
    OPENAI_MODEL_VISION: str = "gpt-4-vision-preview"
    OPENAI_MODEL_FAST: str = "gpt-3.5-turbo"

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_MODEL_PRIMARY: str = "gemini-1.5-pro"
    GEMINI_MODEL_FAST: str = "gemini-1.5-flash"

    # Grok
    GROK_API_KEY: Optional[str] = Field(default=None, env="GROK_API_KEY")

    # AI Processing Settings
    AI_MAX_TOKENS: int = 4000
    AI_TEMPERATURE: float = 0.7
    AI_TIMEOUT: int = 60
    AI_MAX_RETRIES: int = 3

    # ============================================================================
    # Media Storage
    # ============================================================================
    MEDIA_UPLOAD_DIR: str = Field(default="./uploads", env="MEDIA_UPLOAD_DIR")
    MEDIA_MAX_SIZE_MB: int = Field(default=100, env="MEDIA_MAX_SIZE_MB")
    MEDIA_ALLOWED_AUDIO_FORMATS: List[str] = [
        "mp3", "wav", "m4a", "ogg", "flac", "aac"
    ]
    MEDIA_ALLOWED_VIDEO_FORMATS: List[str] = [
        "mp4", "avi", "mov", "mkv", "webm"
    ]
    MEDIA_ALLOWED_IMAGE_FORMATS: List[str] = [
        "png", "jpg", "jpeg", "gif", "webp"
    ]

    # Azure Blob Storage (Optional)
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(
        default=None, env="AZURE_STORAGE_CONNECTION_STRING"
    )
    AZURE_STORAGE_CONTAINER_NAME: str = Field(
        default="meeting-minutes", env="AZURE_STORAGE_CONTAINER_NAME"
    )

    # ============================================================================
    # Email Configuration
    # ============================================================================
    EMAIL_HOST: str = Field(default="smtp.office365.com", env="EMAIL_HOST")
    EMAIL_PORT: int = Field(default=587, env="EMAIL_PORT")
    EMAIL_USER: str = Field(default="noreply@meetingminutes.com", env="EMAIL_USER")
    EMAIL_PASSWORD: str = Field(default="dummy-password", env="EMAIL_PASSWORD")
    EMAIL_USE_TLS: bool = Field(default=True, env="EMAIL_USE_TLS")
    EMAIL_FROM_NAME: str = Field(default="Meeting Minutes Pro", env="EMAIL_FROM_NAME")
    EMAIL_FROM_ADDRESS: str = Field(default="noreply@meetingminutes.com", env="EMAIL_FROM_ADDRESS")

    # ============================================================================
    # Integration APIs
    # ============================================================================
    # Microsoft Graph
    MICROSOFT_GRAPH_CLIENT_ID: Optional[str] = Field(
        default=None, env="MICROSOFT_GRAPH_CLIENT_ID"
    )
    MICROSOFT_GRAPH_CLIENT_SECRET: Optional[str] = Field(
        default=None, env="MICROSOFT_GRAPH_CLIENT_SECRET"
    )
    MICROSOFT_GRAPH_TENANT_ID: Optional[str] = Field(
        default=None, env="MICROSOFT_GRAPH_TENANT_ID"
    )

    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS: Optional[str] = Field(
        default=None, env="GOOGLE_CALENDAR_CREDENTIALS"
    )

    # Slack
    SLACK_BOT_TOKEN: Optional[str] = Field(default=None, env="SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET: Optional[str] = Field(default=None, env="SLACK_SIGNING_SECRET")

    # Jira
    JIRA_SERVER: Optional[str] = Field(default=None, env="JIRA_SERVER")
    JIRA_EMAIL: Optional[str] = Field(default=None, env="JIRA_EMAIL")
    JIRA_API_TOKEN: Optional[str] = Field(default=None, env="JIRA_API_TOKEN")

    # ============================================================================
    # Rate Limiting
    # ============================================================================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # ============================================================================
    # Monitoring & Logging
    # ============================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "json"

    # Sentry
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, env="SENTRY_TRACES_SAMPLE_RATE")

    # Prometheus
    METRICS_ENABLED: bool = True
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")

    # ============================================================================
    # Feature Flags
    # ============================================================================
    FEATURE_AI_TRANSCRIPTION: bool = True
    FEATURE_AI_SENTIMENT: bool = True
    FEATURE_CALENDAR_SYNC: bool = True
    FEATURE_SLACK_INTEGRATION: bool = True
    FEATURE_JIRA_INTEGRATION: bool = True
    FEATURE_REAL_TIME_COLLABORATION: bool = True
    FEATURE_ANALYTICS_DASHBOARD: bool = True

    # ============================================================================
    # Search
    # ============================================================================
    SEARCH_ENABLED: bool = True
    SEARCH_INDEX_PATH: str = Field(default="./search_index", env="SEARCH_INDEX_PATH")

    # Vector Search (Semantic)
    VECTOR_SEARCH_ENABLED: bool = True
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    VECTOR_DIMENSION: int = 1536

    # ============================================================================
    # Analytics
    # ============================================================================
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_RETENTION_DAYS: int = 90

    # ============================================================================
    # Compliance & Data Retention
    # ============================================================================
    DATA_RETENTION_DAYS: int = 365
    AUDIT_LOG_RETENTION_DAYS: int = 730
    GDPR_ENABLED: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create settings instance
settings = Settings()


# Validate critical settings on startup
def validate_settings():
    """Validate that all critical settings are configured"""
    errors = []

    # Check database
    if not all([
        settings.POSTGRES_SERVER,
        settings.POSTGRES_USER,
        settings.POSTGRES_PASSWORD,
        settings.POSTGRES_DB
    ]):
        errors.append("PostgreSQL configuration is incomplete")

    # Check Redis
    if not settings.REDIS_HOST:
        errors.append("Redis configuration is incomplete")

    # Check auth
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")

    # Check AI keys
    if not settings.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is required")

    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required")

    if errors:
        raise ValueError(
            f"Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        )

    return True


if __name__ == "__main__":
    # Test configuration
    try:
        validate_settings()
        print("✓ Configuration validation passed")
        print(f"  - Environment: {settings.ENVIRONMENT}")
        print(f"  - Database: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        print(f"  - Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"  - AI Models: Claude, GPT-4, Gemini")
    except ValueError as e:
        print(f"✗ Configuration validation failed:\n{e}")
        exit(1)
