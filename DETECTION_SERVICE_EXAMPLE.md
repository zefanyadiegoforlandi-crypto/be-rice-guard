"""
Example Detection Service untuk Multiple Diseases Support

Menunjukkan cara detection service harus di-update untuk:
1. Detect multiple diseases dalam 1 foto
2. Return array of diseases dengan confidence dan recommendations
3. Save ke database dengan DetectionDisease records
"""

from typing import List
from app.models.schemas import DiseaseDetectionItem, DetectionCreateResponse
from app.models.database import Detection, DetectionDisease
from sqlalchemy.orm import Session

# ==================== MOCK DETECTION FUNCTION ====================

def mock_detect_diseases(image_path: str) -> List[DiseaseDetectionItem]:
    """
    MOCK FUNCTION: Simulasi AI model yang detect multiple diseases
    
    Real implementation akan gunakan actual ML model (TensorFlow, PyTorch, etc.)
    
    Contoh output dari AI model:
    - Photo bisa contain multiple diseases
    - Each disease punya confidence score
    - Return list, bukan single disease
    """
    
    # Contoh: Foto menunjukkan 2 penyakit
    # (ini mock, real model akan analyze image)
    detected_diseases = [
        DiseaseDetectionItem(
            disease_name="Leaf Blast",
            category="Fungal Disease",
            confidence=0.92,
            recommendations="Spray fungicide containing tricyclazole, Bayleton, or Tilt. Repeat application every 10-14 days.",
            severity="High"
        ),
        DiseaseDetectionItem(
            disease_name="Brown Spot",
            category="Fungal Disease",
            confidence=0.78,
            recommendations="Apply carbendazim, mancozeb, or propiconazole. Improve field drainage and air circulation.",
            severity="Medium"
        ),
    ]
    
    return detected_diseases


def mock_detect_single(image_path: str) -> List[DiseaseDetectionItem]:
    """Contoh: Foto dengan single disease"""
    return [
        DiseaseDetectionItem(
            disease_name="Healthy",
            category="No Disease",
            confidence=0.99,
            recommendations="Plant is healthy! Continue regular maintenance and monitoring.",
            severity="None"
        )
    ]


def mock_detect_pest(image_path: str) -> List[DiseaseDetectionItem]:
    """Contoh: Foto dengan pest + disease"""
    return [
        DiseaseDetectionItem(
            disease_name="Rice Brown Planthopper",
            category="Pest",
            confidence=0.95,
            recommendations="Use insecticides like carbofuran, imidacloprid, or thiamethoxam. Check water level.",
            severity="High"
        ),
        DiseaseDetectionItem(
            disease_name="Leaf Scald",
            category="Bacterial Disease",
            confidence=0.65,
            recommendations="No cure once infected. Use resistant varieties. Practice sanitation.",
            severity="High"
        ),
    ]


# ==================== SAVE TO DATABASE ====================

def save_detection_with_diseases(
    db: Session,
    user_id: int,
    image_filename: str,
    image_path: str,
    detected_diseases: List[DiseaseDetectionItem]
) -> Detection:
    """
    Save detection result dengan multiple diseases ke database
    
    Args:
        db: Database session
        user_id: User ID
        image_filename: e.g., "scan_1707216000.jpg"
        image_path: e.g., "/uploads/user_1/scan_1707216000.jpg"
        detected_diseases: List of DiseaseDetectionItem
        
    Returns:
        Detection object dengan relationships ke DetectionDisease
    """
    
    # 1. Create Detection record
    detection = Detection(
        user_id=user_id,
        image_filename=image_filename,
        image_path=image_path,
        disease_count=len(detected_diseases),
    )
    db.add(detection)
    db.flush()  # Get detection.id
    
    # 2. Create DetectionDisease records untuk setiap disease
    for disease in detected_diseases:
        detection_disease = DetectionDisease(
            detection_id=detection.id,
            disease_name=disease.disease_name,
            category=disease.category,
            confidence=disease.confidence,
            recommendations=disease.recommendations,
            severity=disease.severity,
        )
        db.add(detection_disease)
    
    # 3. Commit semua
    db.commit()
    db.refresh(detection)
    
    return detection


# ==================== RETURN RESPONSE ====================

def format_detection_response(detection: Detection) -> DetectionCreateResponse:
    """
    Format Database Detection object menjadi API response
    
    API response akan include:
    - detection ID
    - image info
    - LIST of diseases (bukan single disease)
    """
    
    # Convert DetectionDisease records menjadi DiseaseDetectionItem
    diseases = [
        DiseaseDetectionItem(
            disease_name=d.disease_name,
            category=d.category,
            confidence=d.confidence,
            recommendations=d.recommendations,
            severity=d.severity,
        )
        for d in detection.diseases  # Dari relationship
    ]
    
    return DetectionCreateResponse(
        id=detection.id,
        image_filename=detection.image_filename,
        image_path=detection.image_path,
        disease_count=detection.disease_count,
        diseases=diseases,  # ARRAY, bukan single
        created_at=detection.created_at,
    )


# ==================== COMPLETE FLOW EXAMPLE ====================

"""
COMPLETE DETECTION FLOW:

1. User upload image ke POST /api/detection/scan

2. Backend:
   a. Save gambar ke filesystem
      - Get user_id dari token
      - Save ke: uploads/user_{user_id}/scan_{timestamp}.jpg
   
   b. Call AI model untuk detect diseases
      - ai_model.predict(image_path) -> List[DiseaseDetectionItem]
      - (contoh di atas)
   
   c. Save ke database dengan multiple records
      - 1 Detection record
      - N DetectionDisease records (1 per disease)
      - Save dengan relationships
   
   d. Format response
      - DetectionCreateResponse dengan list of diseases
      - Include recommendations untuk semua diseases

3. Return response:
{
    "id": 1,
    "image_filename": "scan_1707216000.jpg",
    "image_path": "/uploads/user_1/scan_1707216000.jpg",
    "disease_count": 2,
    "diseases": [
        {
            "disease_name": "Leaf Blast",
            "category": "Fungal Disease",
            "confidence": 0.92,
            "recommendations": "Spray fungicide...",
            "severity": "High"
        },
        {
            "disease_name": "Brown Spot",
            "category": "Fungal Disease",
            "confidence": 0.78,
            "recommendations": "Apply carbendazim...",
            "severity": "Medium"
        }
    ],
    "created_at": "2026-02-07T10:30:00"
}

4. Frontend display:
   - Show disease_count: "2 penyakit terdeteksi"
   - Display cards untuk setiap disease:
     - Disease name + category
     - Confidence percentage (92%, 78%)
     - Recommendations untuk treatment
     - Severity indicator
"""
