"""Sessions API endpoints."""

from fastapi import APIRouter, HTTPException, status

from ...core import get_session_manager, Orchestrator
from ...models import Session
from ..schemas import CreateSessionRequest, CreateSessionResponse, RunSessionRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Shared orchestrator instance
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    """Get the shared orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@router.post(
    "",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
)
async def create_session(request: CreateSessionRequest) -> CreateSessionResponse:
    """Create a new empty session.

    Args:
        request: Session creation parameters.

    Returns:
        Created session ID.
    """
    manager = get_session_manager()
    session = manager.create_session(language=request.language)

    return CreateSessionResponse(session_id=session.session_id)


@router.get(
    "/{session_id}",
    response_model=Session,
    summary="Get session by ID",
    responses={
        404: {"description": "Session not found"},
    },
)
async def get_session(session_id: str) -> Session:
    """Get a session by its ID.

    Args:
        session_id: The session UUID.

    Returns:
        Full session data.

    Raises:
        HTTPException: 404 if session not found.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    return session


@router.get(
    "",
    response_model=list[str],
    summary="List all session IDs",
)
async def list_sessions() -> list[str]:
    """List all available session IDs.

    Returns:
        List of session IDs.
    """
    manager = get_session_manager()
    return manager.list_sessions()


@router.post(
    "/{session_id}/run",
    response_model=Session,
    summary="Run a search in a session",
    responses={
        404: {"description": "Session not found"},
    },
)
async def run_session(session_id: str, request: RunSessionRequest) -> Session:
    """Execute a search query and update the session.

    Args:
        session_id: The session UUID.
        request: Run parameters including the search query.

    Returns:
        Updated session with search results.

    Raises:
        HTTPException: 404 if session not found.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Run search and update session
    orchestrator = Orchestrator(use_mock=request.use_mock)
    updated_session = orchestrator.run_session(session, request.query)

    return updated_session
