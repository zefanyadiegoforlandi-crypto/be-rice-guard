from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Header, Depends, Query
from typing import Optional
from datetime import datetime
from app.services.detection_service import DetectionService
from app.utils.security import decode_access_token
from app.models.schemas import DiseaseDetectionItem, UpdateImageNameRequest, PaginatedDetectionHistoryResponse
from app.models.database import User, Detection, DetectionDisease
from app.models.database_init import get_db
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
import math
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


def get_current_user_optional(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """Extract user from authorization header (optional) - return None jika tidak ada auth"""
    if not authorization:
        return None

    # Extract token dari "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
    except ValueError:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    email = payload.get("sub")
    if not email:
        return None

    # Get user dari database
    user = db.query(User).filter(User.email == email).first()
    return user if user else None


@router.post("/scan")
async def scan_image(
    file: UploadFile = File(...),
    image_name: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Upload and scan rice plant image for disease/pest detection
    
    Support 2 jalur:
    1. Dengan login (Authorization header) → hasil disimpan ke database
    2. Tanpa login (guest) → hasil hanya dikembalikan, tidak disimpan
    """

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

    # Save image ke folder user (atau guest)
    user_id = current_user.id if current_user else None
    image_filename, image_path, absolute_path = DetectionService.save_uploaded_image(
        content, file.filename, user_id
    )
    if not image_filename or not absolute_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image to disk"
        )

    # Validate image file exists dan readable
    if not os.path.exists(absolute_path):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image file not found after saving"
        )

    # Perform detection menggunakan YOLO model - returns multiple diseases + annotated image
    try:
        diseases, annotated_image_path = DetectionService.detect_diseases(absolute_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection failed: {str(e)}"
        )
    
    if not diseases:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Detection returned no results"
        )

    # Simpan ke database (baik login maupun guest) - admin butuh bisa lihat semua data
    detection = DetectionService.save_detection_to_db(
        db=db,
        user_id=current_user.id if current_user else None,  # None untuk guest scan
        image_filename=image_filename,
        image_path=image_path,
        diseases=diseases,
        annotated_image_path=annotated_image_path,
        image_name=image_name,
        original_filename=file.filename,
        file_size=len(content),
        mime_type=file.content_type
    )
    detection_id = detection.id
    created_at = detection.created_at.isoformat() if detection.created_at else None

    # Return response dengan multiple diseases + annotated image
    return {
        "id": detection_id,
        "image_name": image_name,
        "image_filename": image_filename,
        "image_path": image_path,
        "annotated_image_path": annotated_image_path,
        "disease_count": len(diseases),
        "diseases": [
            {
                "disease_name": d.disease_name,
                "category": d.category,
                "confidence": d.confidence,
                "recommendations": DetectionService.get_recommendations_text(d.disease_name, d.recommendations),
                "severity": d.severity,
                "bbox": d.bbox,
            }
            for d in diseases
        ],
        "created_at": created_at,
    }


@router.get("/history", response_model=PaginatedDetectionHistoryResponse)
async def get_detection_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    sort_by: str = Query("date", pattern="^(date|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    disease: Optional[str] = Query(None),
):
    """Get user's detection history"""
    query = db.query(Detection).filter(Detection.user_id == current_user.id)

    if disease and disease.strip():
        disease_pattern = f"%{disease.strip()}%"
        query = query.filter(
            Detection.id.in_(
                db.query(DetectionDisease.detection_id)
                .filter(DetectionDisease.disease_name.ilike(disease_pattern))
                .distinct()
            )
        )

    if sort_by == "name":
        name_expr = func.coalesce(Detection.image_name, Detection.image_filename)
        primary_order = name_expr.asc() if sort_order == "asc" else name_expr.desc()
        secondary_order = Detection.created_at.asc() if sort_order == "asc" else Detection.created_at.desc()
        query = query.order_by(primary_order, secondary_order)
    else:
        query = query.order_by(Detection.created_at.asc() if sort_order == "asc" else Detection.created_at.desc())

    total = query.count()
    total_pages = math.ceil(total / per_page) if total else 0
    page = min(page, total_pages) if total_pages else 1

    detections = query.options(selectinload(Detection.diseases)).offset((page - 1) * per_page).limit(per_page).all()

    items = []
    for det in detections:
        items.append({
            "id": det.id,
            "image_name": det.image_name,
            "image_filename": det.image_filename,
            "image_path": det.image_path,
            "annotated_image_path": det.annotated_image_path,
            "disease_count": det.disease_count,
            "diseases": [
                {
                    "disease_name": d.disease_name,
                    "category": d.category,
                    "confidence": d.confidence,
                    "recommendations": DetectionService.get_recommendations_text(d.disease_name, d.recommendations),
                    "severity": d.severity,
                    "bbox": d.bbox,
                }
                for d in det.diseases
            ],
            "created_at": det.created_at.isoformat() if det.created_at else None,
        })

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "items": items,
    }


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
