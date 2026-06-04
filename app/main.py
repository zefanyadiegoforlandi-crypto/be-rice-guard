from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import CORS_ORIGINS, UPLOADS_DIR, USE_DATABASE, YOLO_MODEL_PATH
from app.routes import auth, detection, health, admin

# Create FastAPI app
app = FastAPI(
    title="Rice Disease & Pest Detection API",
    description="API for detecting diseases and pests in rice plants using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(detection.router)
app.include_router(admin.router)

# Mount uploads directory for serving images
if os.path.exists(UPLOADS_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Ensure directories exist
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    # Initialize database if enabled
    if USE_DATABASE:
        try:
            from app.models.database_init import init_db
            init_db()
            print("✓ Database initialized successfully")
        except Exception as e:
            print(f"⚠ Database initialization warning: {e}")
            print("  Using legacy JSON storage if database unavailable")
    
    # Load YOLO model
    try:
        from app.services.detection_service import load_yolo_model
        load_yolo_model()
    except FileNotFoundError:
        print(f"⚠ YOLO model not found at {YOLO_MODEL_PATH}")
        print("  Detection will fail until best.pt is placed in backend/ml_models/")
    except Exception as e:
        print(f"⚠ Failed to load YOLO model: {e}")

    print("✓ Application started successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
