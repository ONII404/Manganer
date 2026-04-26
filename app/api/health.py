# app/api/health.py
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["System"])

class HealthResponse(BaseModel):
    status: str
    message: str = "OK"
    version: str = "0.1.0"

@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health endpoint minimalista: sin I/O, sin métricas, sin riesgos."""
    return HealthResponse(status="ok", message="Manganer API is running")