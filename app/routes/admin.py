from fastapi import APIRouter, HTTPException, Depends, Header, status, Query
from typing import Optional, List
from app.models.schemas import UserResponse, PaginatedUserResponse, PaginatedDetectionHistoryResponse, ChangePasswordRequest
from app.models.database import User, Detection, DetectionDisease
from app.utils.security import decode_access_token, hash_password
from app.models.database_init import get_db
from app.services.detection_service import DetectionService
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from pydantic import BaseModel
import os
import math

router = APIRouter(prefix="/api/admin", tags=["admin"])

class UpdateUserRequest(BaseModel):
    """Update user request - admin dapat edit name saja, password tidak"""
    name: Optional[str] = None

class UserDetailResponse(BaseModel):
    """User detail with detection history"""
    id: int
    email: str
    name: str
    role: str
    created_at: str
    total_detections: int
    detections: list

    class Config:
        from_attributes = True

def get_admin_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Extract admin user from token and verify role"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

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

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is admin
    if user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


@router.get("/users", response_model=PaginatedUserResponse)
async def get_all_users(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
):
    """Get all users (admin only)"""
    query = db.query(User)
    order_expr = func.lower(User.name).asc() if sort_order == "asc" else func.lower(User.name).desc()
    total = query.count()
    total_pages = math.ceil(total / per_page) if total else 0
    page = min(page, total_pages) if total_pages else 1
    users = query.order_by(order_expr, User.id.asc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "items": [
            UserResponse(
                id=u.id,
                email=u.email,
                name=u.name,
                role=u.role,
                created_at=u.created_at
            )
            for u in users
        ],
    }


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get user detail with detection history (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    detections = db.query(Detection).filter(Detection.user_id == user_id).order_by(Detection.created_at.desc()).all()
    
    detection_list = [
        {
            "id": d.id,
            "image_name": d.image_name,
            "image_filename": d.image_filename,
            "image_path": d.image_path,
            "annotated_image_path": d.annotated_image_path,
            "disease_count": d.disease_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "diseases": [
                {
                    "disease_name": disease.disease_name,
                    "category": disease.category,
                    "confidence": disease.confidence,
                    "recommendations": DetectionService.get_recommendations_text(disease.disease_name, disease.recommendations),
                    "severity": disease.severity
                }
                for disease in d.diseases
            ]
        }
        for d in detections
    ]

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
        total_detections=len(detections),
        detections=detection_list
    )


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    body: UpdateUserRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user name (admin only) - password tidak bisa diubah dari admin"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if body.name:
        if not body.name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name cannot be empty"
            )
        user.name = body.name.strip()

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        created_at=user.created_at
    )


@router.put("/users/{user_id}/password")
async def update_user_password(
    user_id: int,
    body: ChangePasswordRequest,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user password (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not body.new_password or len(body.new_password.strip()) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password baru minimal 6 karakter"
        )

    user.password_hash = hash_password(body.new_password.strip())
    db.commit()

    return {"message": "Password user berhasil diupdate"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user is disabled for admin"""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin tidak diperbolehkan menghapus user"
    )


@router.get("/stats")
async def get_admin_stats(admin_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """Get admin dashboard statistics"""
    total_users = db.query(User).filter(User.role == 'user').count()
    total_scans = db.query(Detection).count()
    total_guest_scans = db.query(Detection).filter(Detection.user_id.is_(None)).count()
    
    return {
        "total_users": total_users,
        "total_scans": total_scans,
        "total_registered_scans": total_scans - total_guest_scans,
        "total_guest_scans": total_guest_scans
    }


@router.get("/guest-scans", response_model=PaginatedDetectionHistoryResponse)
async def get_guest_scans(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    sort_by: str = Query("date", pattern="^(date|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    disease: Optional[str] = Query(None),
):
    """Get all guest scans (admin only)"""
    query = db.query(Detection).filter(Detection.user_id.is_(None))

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
    guest_detections = query.options(selectinload(Detection.diseases)).offset((page - 1) * per_page).limit(per_page).all()
    
    detections = [
        {
            "id": d.id,
            "image_name": d.image_name,
            "image_filename": d.image_filename,
            "image_path": d.image_path,
            "annotated_image_path": d.annotated_image_path,
            "disease_count": d.disease_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "diseases": [
                {
                    "disease_name": disease.disease_name,
                    "category": disease.category,
                    "confidence": disease.confidence,
                    "recommendations": DetectionService.get_recommendations_text(disease.disease_name, disease.recommendations),
                    "severity": disease.severity,
                    "bbox": disease.bbox
                }
                for disease in d.diseases
            ]
        }
        for d in guest_detections
    ]
    
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "items": detections,
    }


@router.delete("/detections/{detection_id}")
async def delete_detection(
    detection_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a detection by ID (admin only) - dapat menghapus scan user maupun guest"""
    from app.config import UPLOADS_DIR
    
    detection = db.query(Detection).filter(Detection.id == detection_id).first()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Hapus file gambar asli jika ada
    if detection.image_path:
        try:
            image_abs_path = os.path.join(UPLOADS_DIR, detection.image_path.lstrip('/').replace('uploads/', ''))
            if os.path.exists(image_abs_path):
                os.remove(image_abs_path)
        except Exception as e:
            print(f"Error deleting image file: {e}")
    
    # Hapus file annotated image jika ada
    if detection.annotated_image_path:
        try:
            annotated_abs_path = os.path.join(UPLOADS_DIR, detection.annotated_image_path.lstrip('/').replace('uploads/', ''))
            if os.path.exists(annotated_abs_path):
                os.remove(annotated_abs_path)
        except Exception as e:
            print(f"Error deleting annotated image file: {e}")
    
    # Hapus dari database (cascade akan menghapus diseases dan image_metadata)
    db.delete(detection)
    db.commit()
    
    return {"message": f"Detection {detection_id} deleted successfully"}
