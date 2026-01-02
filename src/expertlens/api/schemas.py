"""API request/response schemas.

These Pydantic models define the API contract.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# Request schemas
class CreateSessionRequest(BaseModel):
    """Request body for creating a new session."""

    language: str = Field(default="ko", description="Session language (ko, en)")


class RunSessionRequest(BaseModel):
    """Request body for running a search in a session."""

    query: str = Field(..., description="Search query to execute")


# Response schemas
class CreateSessionResponse(BaseModel):
    """Response for session creation."""

    session_id: str = Field(..., description="Created session ID")


class SessionInfoResponse(BaseModel):
    """Brief session info response."""

    session_id: str
    language: str
    query: str
    created_at: datetime
    updated_at: datetime
    expert_count: int
    evidence_count: int
    company_count: int


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error message")
