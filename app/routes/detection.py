from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Header, Depends
from typing import Optional
from app.services.detection_service import DetectionService
from app.utils.security import decode_access_token
from app.models.schemas import DiseaseDetectionItem, UpdateImageNameRequest
from app.models.database import User, Detection
from app.models.database_init import get_db
from sqlalchemy.orm import Session
import os

router = APIRouter(prefix="/api/detection", tags=["detection"])


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Extract user from authorization header dan return User object dari database"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in token"
        )

    # Get user dari database
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


@router.post("/scan")
async def scan_image(
    file: UploadFile = File(...),
    image_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and scan rice plant image for disease/pest detection"""

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )

    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Read file content
    try:
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large (max 10MB)"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading file: {str(e)}"
        )

    # Save image ke folder user
    image_filename, image_path = DetectionService.save_uploaded_image(
        content, file.filename, current_user.id
    )
    if not image_filename:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image"
        )

    # Perform detection - returns multiple diseases
    diseases = DetectionService.detect_diseases(image_path)
    if not diseases:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detection failed"
        )

    # Save to database dengan multiple diseases
    detection = DetectionService.save_detection_to_db(
        db=db,
        user_id=current_user.id,
        image_filename=image_filename,
        image_path=image_path,
        diseases=diseases,
        image_name=image_name,
        original_filename=file.filename,
        file_size=len(content),
        mime_type=file.content_type
    )

    # Return response dengan multiple diseases
    return {
        "id": detection.id,
        "image_name": detection.image_name,
        "image_filename": detection.image_filename,
        "image_path": detection.image_path,
        "disease_count": detection.disease_count,
        "diseases": [
            {
                "disease_name": d.disease_name,
                "category": d.category,
                "confidence": d.confidence,
                "recommendations": d.recommendations,
                "severity": d.severity,
            }
            for d in detection.diseases
        ],
        "created_at": detection.created_at.isoformat() if detection.created_at else None,
    }


@router.get("/history")
async def get_detection_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's detection history"""
    detections = DetectionService.get_user_detections(db, current_user.id)

    items = []
    for det in detections:
        items.append({
            "id": det.id,
            "image_name": det.image_name,
            "image_filename": det.image_filename,
            "image_path": det.image_path,
            "disease_count": det.disease_count,
            "diseases": [
                {
                    "disease_name": d.disease_name,
                    "category": d.category,
                    "confidence": d.confidence,
                    "recommendations": d.recommendations,
                    "severity": d.severity,
                }
                for d in det.diseases
            ],
            "created_at": det.created_at.isoformat() if det.created_at else None,
        })

    return {"total": len(items), "items": items}


@router.get("/stats")
async def get_detection_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's detection statistics"""
    stats = DetectionService.get_detection_stats(db, current_user.id)
    return stats


@router.patch("/history/{detection_id}/rename")
async def rename_detection(
    detection_id: int,
    body: UpdateImageNameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rename / label a detection image"""
    detection = db.query(Detection).filter(
        Detection.id == detection_id,
        Detection.user_id == current_user.id
    ).first()
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    detection.image_name = body.image_name.strip()
    db.commit()
    return {"message": "Nama berhasil diubah", "id": detection_id, "image_name": detection.image_name}


@router.delete("/history/{detection_id}")
async def delete_detection(
    detection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a single detection by id"""
    success = DetectionService.delete_detection(db, detection_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    return {"message": "Detection deleted", "id": detection_id}


@router.delete("/history")
async def delete_all_detections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all detections for current user"""
    count = DetectionService.delete_all_detections(db, current_user.id)
    return {"message": f"{count} detections deleted", "count": count}
