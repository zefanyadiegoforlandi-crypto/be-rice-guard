from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ===================== USER SCHEMAS =====================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

class UpdateNameRequest(BaseModel):
    """Update name request"""
    name: str

class ChangePasswordRequest(BaseModel):
    """Change password request"""
    new_password: str

class UserResponse(BaseModel):
    """User response"""
    id: Optional[int] = None
    email: str
    name: str
    role: Optional[str] = 'user'  # 'user' atau 'admin'
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    token_type: str
    user: UserResponse

# ===================== DISEASE SCHEMAS =====================

class DiseaseDetectionItem(BaseModel):
    """Single disease detection result"""
    disease_name: str
    category: Optional[str] = None
    confidence: float  # 0.0 - 1.0
    recommendations: Optional[str] = None
    severity: Optional[str] = None  # "Low", "Medium", "High"
    bbox: Optional[List[float]] = None  # Bounding box [x1, y1, x2, y2]

    class Config:
        from_attributes = True

# ===================== DETECTION SCHEMAS =====================

class DetectionRequest(BaseModel):
    """Detection request"""
    # Image will be sent as file, not in body
    pass

class ImageMetadataResponse(BaseModel):
    """Image metadata response"""
    id: Optional[int] = None
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UpdateImageNameRequest(BaseModel):
    """Request to rename image label"""
    image_name: str

class DetectionResponse(BaseModel):
    """Detection result response - dengan multiple diseases"""
    id: int
    user_id: int
    image_name: Optional[str] = None
    image_filename: str
    image_path: str
    annotated_image_path: Optional[str] = None
    disease_count: int
    diseases: List[DiseaseDetectionItem]  # BARU: array of diseases
    created_at: datetime
    image_metadata: Optional[List[ImageMetadataResponse]] = None

    class Config:
        from_attributes = True

class DetectionCreateResponse(BaseModel):
    """Detection create response - untuk scan endpoint"""
    id: int
    image_name: Optional[str] = None
    image_filename: str
    image_path: str
    annotated_image_path: Optional[str] = None
    disease_count: int
    diseases: List[DiseaseDetectionItem]  # Multiple diseases per scan
    created_at: datetime

    class Config:
        from_attributes = True

class DetectionHistoryItem(BaseModel):
    """Single history item - dengan multiple diseases"""
    id: int
    image_name: Optional[str] = None
    disease_count: int
    diseases: List[DiseaseDetectionItem]  # Show all detected diseases
    created_at: datetime
    image_path: str
    annotated_image_path: Optional[str] = None
    image_filename: str

    class Config:
        from_attributes = True

class DetectionHistoryResponse(BaseModel):
    """Detection history list response"""
    total: int
    items: List[DetectionHistoryItem]


class PaginatedDetectionHistoryResponse(BaseModel):
    """Paginated detection history response"""
    total: int
    page: int
    per_page: int
    total_pages: int
    items: List[DetectionHistoryItem]


class PaginatedUserResponse(BaseModel):
    """Paginated user list response"""
    total: int
    page: int
    per_page: int
    total_pages: int
    items: List[UserResponse]

