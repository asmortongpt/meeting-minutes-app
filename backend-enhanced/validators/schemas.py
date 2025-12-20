# backend-enhanced/validators/schemas.py

"""
This module defines Pydantic schemas for input validation across the application.
It ensures data integrity, enforces security constraints, and prevents common
vulnerabilities like injection attacks by validating and sanitizing inputs.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, constr, validator
import re
from datetime import datetime


class BaseSchema(BaseModel):
    """
    Base schema with common configuration for all models.
    Includes security-focused settings to prevent injection and ensure data integrity.
    """
    class Config:
        # Prevent arbitrary code execution by disallowing extra fields
        extra = "forbid"
        # Enable ORM mode for easy integration with database models
        orm_mode = True


class UserRegistrationSchema(BaseSchema):
    """
    Schema for user registration data validation.
    Enforces strong password policies and sanitizes input fields.
    """
    username: constr(min_length=3, max_length=50, strip_whitespace=True) = Field(
        ..., description="Username must be between 3 and 50 characters"
    )
    email: EmailStr = Field(..., description="Valid email address")
    password: constr(min_length=8, max_length=128) = Field(
        ..., description="Password must be at least 8 characters long"
    )

    @validator("username")
    def validate_username(cls, value: str) -> str:
        """
        Validate username to prevent injection attacks and invalid characters.
        Only alphanumeric characters and underscores are allowed.
        """
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return value

    @validator("password")
    def validate_password(cls, value: str) -> str:
        """
        Enforce strong password policy:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class UserLoginSchema(BaseSchema):
    """
    Schema for user login data validation.
    Sanitizes input to prevent injection attacks.
    """
    email: EmailStr = Field(..., description="Valid email address")
    password: constr(min_length=8, max_length=128) = Field(
        ..., description="Password must be at least 8 characters long"
    )


class UserUpdateSchema(BaseSchema):
    """
    Schema for updating user profile data.
    All fields are optional to allow partial updates.
    """
    username: Optional[constr(min_length=3, max_length=50, strip_whitespace=True)] = None
    email: Optional[EmailStr] = None

    @validator("username", always=True)
    def validate_username(cls, value: Optional[str]) -> Optional[str]:
        """
        Validate username if provided, ensuring no invalid characters.
        """
        if value is not None:
            if not re.match(r"^[a-zA-Z0-9_]+$", value):
                raise ValueError("Username can only contain letters, numbers, and underscores")
        return value


class PostCreateSchema(BaseSchema):
    """
    Schema for creating a new post.
    Includes validation to prevent XSS by sanitizing content.
    """
    title: constr(min_length=1, max_length=200, strip_whitespace=True) = Field(
        ..., description="Post title must be between 1 and 200 characters"
    )
    content: constr(min_length=1, strip_whitespace=True) = Field(
        ..., description="Post content cannot be empty"
    )

    @validator("title")
    def sanitize_title(cls, value: str) -> str:
        """
        Sanitize title to prevent XSS by removing potentially malicious content.
        Strips any HTML tags or script content.
        """
        # Basic sanitization - remove any HTML tags
        clean_title = re.sub(r"<[^>]+>", "", value)
        if not clean_title:
            raise ValueError("Title cannot be empty after sanitization")
        return clean_title

    @validator("content")
    def sanitize_content(cls, value: str) -> str:
        """
        Sanitize content to prevent XSS by removing potentially malicious scripts.
        Allows basic formatting but removes script tags and dangerous attributes.
        """
        # Remove script tags and dangerous attributes
        clean_content = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", value)
        clean_content = re.sub(r"on\w*=\"[^\"]*\"", "", clean_content)
        if not clean_content.strip():
            raise ValueError("Content cannot be empty after sanitization")
        return clean_content


class PostUpdateSchema(BaseSchema):
    """
    Schema for updating an existing post.
    All fields are optional for partial updates.
    """
    title: Optional[constr(min_length=1, max_length=200, strip_whitespace=True)] = None
    content: Optional[constr(min_length=1, strip_whitespace=True)] = None

    @validator("title", always=True)
    def sanitize_title(cls, value: Optional[str]) -> Optional[str]:
        """
        Sanitize title if provided to prevent XSS.
        """
        if value is not None:
            clean_title = re.sub(r"<[^>]+>", "", value)
            if not clean_title:
                raise ValueError("Title cannot be empty after sanitization")
            return clean_title
        return value

    @validator("content", always=True)
    def sanitize_content(cls, value: Optional[str]) -> Optional[str]:
        """
        Sanitize content if provided to prevent XSS.
        """
        if value is not None:
            clean_content = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", value)
            clean_content = re.sub(r"on\w*=\"[^\"]*\"", "", clean_content)
            if not clean_content.strip():
                raise ValueError("Content cannot be empty after sanitization")
            return clean_content
        return value


class CommentCreateSchema(BaseSchema):
    """
    Schema for creating a new comment on a post.
    Includes sanitization to prevent XSS.
    """
    content: constr(min_length=1, max_length=1000, strip_whitespace=True) = Field(
        ..., description="Comment content must be between 1 and 1000 characters"
    )

    @validator("content")
    def sanitize_content(cls, value: str) -> str:
        """
        Sanitize comment content to prevent XSS by removing malicious scripts.
        """
        clean_content = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", value)
        clean_content = re.sub(r"on\w*=\"[^\"]*\"", "", clean_content)
        if not clean_content.strip():
            raise ValueError("Comment content cannot be empty after sanitization")
        return clean_content


class TokenSchema(BaseSchema):
    """
    Schema for token response data.
    Used for returning JWT tokens after authentication.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenDataSchema(BaseSchema):
    """
    Schema for token payload data.
    Used for decoding and validating JWT tokens.
    """
    email: Optional[str] = None
    user_id: Optional[int] = None