from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Rice Detection API is running"
    }

@router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Rice Disease & Pest Detection API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "detection": "/api/detection",
            "docs": "/docs"
        }
    }
