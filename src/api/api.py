"This module defines the API routes for the FastAPI application." ""
from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
def hello() -> dict:
    """Return a greeting message."""
    return {"message": "Hello from FastAPI!"}
