"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    """Health check endpoint.

    Returns:
        Status object indicating service health.
    """
    return {"status": "ok"}
