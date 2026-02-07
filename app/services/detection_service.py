import os
import uuid
import time
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from PIL import Image
import random
from app.config import UPLOADS_DIR, COMMON_ISSUES
from app.models.database import Detection, DetectionDisease, ImageMetadata
from app.models.schemas import DiseaseDetectionItem
from sqlalchemy.orm import Session


class DetectionService:
    """Handle disease and pest detection operations with MySQL database"""

    @staticmethod
    def save_uploaded_image(file_content: bytes, filename: str, user_id: int) -> Tuple[str, str]:
        """
        Save uploaded image ke folder user dan return (filename, relative_path)
        Format: uploads/user_{id}/scan_{timestamp}.ext
        """
        try:
            file_ext = os.path.splitext(filename)[1].lower() or '.jpg'
            timestamp = int(time.time())
            unique_filename = f"scan_{timestamp}{file_ext}"

            # Buat folder per user
            user_folder = os.path.join(UPLOADS_DIR, f"user_{user_id}")
            os.makedirs(user_folder, exist_ok=True)

            file_path = os.path.join(user_folder, unique_filename)

            with open(file_path, 'wb') as f:
                f.write(file_content)

            relative_path = f"/uploads/user_{user_id}/{unique_filename}"
            return unique_filename, relative_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None

    @staticmethod
    def detect_diseases(image_path: str) -> List[DiseaseDetectionItem]:
        """
        Detect multiple diseases dari image
        MOCK: Randomly select 1-3 diseases
        Real implementation: gunakan AI model
        """
        try:
            # Mock: random select 1-3 diseases
            num_diseases = random.choice([1, 1, 1, 2, 2, 3])  # Weighted: mostly 1-2
            selected = random.sample(COMMON_ISSUES, min(num_diseases, len(COMMON_ISSUES)))

            diseases = []
            for item in selected:
                confidence = min(item['confidence'] + random.uniform(-0.05, 0.05), 1.0)
                confidence = max(confidence, 0.0)

                recommendations = DetectionService.get_recommendations(item['name'])
                rec_text = " | ".join(recommendations)

                severity = "High" if confidence >= 0.85 else "Medium" if confidence >= 0.7 else "Low"
                if item['name'] == "Healthy":
                    severity = "None"

                diseases.append(DiseaseDetectionItem(
                    disease_name=item['name'],
                    category=item['type'].capitalize(),
                    confidence=round(confidence, 4),
                    recommendations=rec_text,
                    severity=severity
                ))

            return diseases
        except Exception as e:
            print(f"Error during detection: {e}")
            return []

    @staticmethod
    def get_recommendations(disease_name: str) -> List[str]:
        """Get treatment recommendations based on disease"""
        recommendations_map = {
            "Leaf Blast": [
                "Apply fungicide immediately",
                "Increase field ventilation",
                "Reduce nitrogen fertilizer",
                "Remove infected leaves",
                "Maintain proper water management"
            ],
            "Brown Spot": [
                "Use resistant varieties",
                "Apply copper fungicide",
                "Improve drainage",
                "Remove crop residue",
                "Avoid continuous monoculture"
            ],
            "Bacterial Leaf Blight": [
                "Cut infected leaves",
                "Use antibiotic spray",
                "Improve water management",
                "Destroy infected plants",
                "Practice crop rotation"
            ],
            "Rice Brown Planthopper": [
                "Use yellow sticky traps",
                "Apply insecticide spray",
                "Introduce natural predators",
                "Maintain field hygiene",
                "Use resistant varieties"
            ],
            "Rice Leafhopper": [
                "Apply neem oil spray",
                "Remove weeds",
                "Use light traps",
                "Apply systemic insecticide",
                "Maintain water level"
            ],
            "Rice Case Worm": [
                "Drain field water temporarily",
                "Apply biological insecticide",
                "Maintain proper water depth",
                "Introduce natural enemies",
                "Practice clean cultivation"
            ],
            "Healthy": [
                "Continue regular monitoring",
                "Maintain proper nutrition",
                "Ensure good water management",
                "Prevent pest infestation",
                "Keep field clean"
            ]
        }

        return recommendations_map.get(disease_name, ["Monitor plant regularly"])

    @staticmethod
    def save_detection_to_db(
        db: Session,
        user_id: int,
        image_filename: str,
        image_path: str,
        diseases: List[DiseaseDetectionItem],
        image_name: str = None,
        original_filename: str = None,
        file_size: int = None,
        mime_type: str = None
    ) -> Detection:
        """Save detection result dengan multiple diseases ke database"""

        # Auto-generate default name "Gambar #N" — N = total deteksi user + 1
        if not image_name or not image_name.strip():
            total = db.query(Detection).filter(Detection.user_id == user_id).count()
            image_name = f"Gambar #{total + 1}"

        # 1. Create Detection record
        detection = Detection(
            user_id=user_id,
            image_name=image_name.strip(),
            image_filename=image_filename,
            image_path=image_path,
            disease_count=len(diseases),
        )
        db.add(detection)
        db.flush()  # Get detection.id

        # 2. Create DetectionDisease records untuk setiap disease
        for disease in diseases:
            detection_disease = DetectionDisease(
                detection_id=detection.id,
                disease_name=disease.disease_name,
                category=disease.category,
                confidence=disease.confidence,
                recommendations=disease.recommendations,
                severity=disease.severity,
            )
            db.add(detection_disease)

        # 3. Save image metadata (optional)
        if original_filename or file_size:
            metadata = ImageMetadata(
                detection_id=detection.id,
                original_filename=original_filename,
                file_size=file_size,
                mime_type=mime_type,
            )
            db.add(metadata)

        # 4. Commit
        db.commit()
        db.refresh(detection)

        return detection

    @staticmethod
    def get_user_detections(db: Session, user_id: int) -> List[Detection]:
        """Get all detections untuk user dari database"""
        return db.query(Detection).filter(
            Detection.user_id == user_id
        ).order_by(Detection.created_at.desc()).all()

    @staticmethod
    def get_detection_by_id(db: Session, detection_id: int, user_id: int) -> Optional[Detection]:
        """Get single detection by id"""
        return db.query(Detection).filter(
            Detection.id == detection_id,
            Detection.user_id == user_id
        ).first()

    @staticmethod
    def get_detection_stats(db: Session, user_id: int) -> Dict:
        """Get detection statistics for user"""
        detections = db.query(Detection).filter(
            Detection.user_id == user_id
        ).order_by(Detection.created_at.desc()).all()

        total = len(detections)

        # Count unique disease types across all detections
        all_diseases = []
        disease_names_count = {}
        for det in detections:
            for d in det.diseases:
                all_diseases.append(d)
                name = d.disease_name or 'Unknown'
                disease_names_count[name] = disease_names_count.get(name, 0) + 1

        disease_count = sum(1 for d in all_diseases if d.category and d.category.lower() == 'disease')
        pest_count = sum(1 for d in all_diseases if d.category and d.category.lower() == 'pest')
        healthy_count = sum(1 for d in all_diseases if d.disease_name == 'Healthy')

        # Recent 5 detections summary
        recent = []
        for det in detections[:5]:
            diseases_list = [
                {
                    'disease_name': d.disease_name,
                    'category': d.category,
                    'confidence': d.confidence,
                }
                for d in det.diseases
            ]
            recent.append({
                'id': det.id,
                'image_name': det.image_name,
                'created_at': det.created_at.isoformat() if det.created_at else None,
                'disease_count': len(det.diseases),
                'diseases': diseases_list,
            })

        return {
            'total_scans': total,
            'diseases_found': disease_count,
            'pests_found': pest_count,
            'healthy_plants': healthy_count,
            'disease_breakdown': disease_names_count,
            'recent_detections': recent,
        }

    @staticmethod
    def delete_detection(db: Session, detection_id: int, user_id: int) -> bool:
        """Delete single detection by id (+ cascade diseases, metadata, file)"""
        detection = db.query(Detection).filter(
            Detection.id == detection_id,
            Detection.user_id == user_id
        ).first()
        if not detection:
            return False

        # Delete image file from disk
        DetectionService._delete_image_file(detection.image_path)

        db.delete(detection)
        db.commit()
        return True

    @staticmethod
    def delete_all_detections(db: Session, user_id: int) -> int:
        """Delete all detections for user, return count deleted"""
        detections = db.query(Detection).filter(
            Detection.user_id == user_id
        ).all()

        count = len(detections)
        for det in detections:
            DetectionService._delete_image_file(det.image_path)
            db.delete(det)

        db.commit()
        return count

    @staticmethod
    def _delete_image_file(image_path: str):
        """Delete image file from disk"""
        if not image_path:
            return
        try:
            # image_path = "/uploads/user_1/scan_xxx.jpg"
            relative = image_path.lstrip('/')
            full_path = os.path.join(os.path.dirname(UPLOADS_DIR), relative)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            print(f"Warning: could not delete file {image_path}: {e}")
