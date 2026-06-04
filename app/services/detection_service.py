import os
import uuid
import time
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from PIL import Image
from app.config import (
    UPLOADS_DIR, YOLO_MODEL_PATH, YOLO_CONFIDENCE_THRESHOLD,
    CLASS_CATEGORIES, CLASS_RECOMMENDATIONS, get_severity,
)
from app.models.database import Detection, DetectionDisease, ImageMetadata
from app.models.schemas import DiseaseDetectionItem
from sqlalchemy.orm import Session


# ── Singleton YOLO model ─────────────────────────────────────────────
_yolo_model = None


def load_yolo_model():
    """Load YOLO model once (singleton) agar tidak reload tiap request."""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        if not os.path.exists(YOLO_MODEL_PATH):
            raise FileNotFoundError(f"Model not found: {YOLO_MODEL_PATH}")
        _yolo_model = YOLO(YOLO_MODEL_PATH)
        print(f"✓ YOLO model loaded from {YOLO_MODEL_PATH}")
        print(f"  Classes: {_yolo_model.names}")
    return _yolo_model


def get_yolo_model():
    """Ambil model yang sudah di-load."""
    global _yolo_model
    if _yolo_model is None:
        return load_yolo_model()
    return _yolo_model


class DetectionService:
    """Handle disease detection operations with YOLO model and MySQL database"""

    @staticmethod
    def save_uploaded_image(file_content: bytes, filename: str, user_id: Optional[int] = None) -> Tuple[str, str, str]:
        """
        Save uploaded image ke folder user (atau guest untuk anonymous scan)
        Format: uploads/user_{id}/scan_{timestamp}.ext (untuk user dengan ID)
                uploads/guest/scan_{timestamp}.ext (untuk guest scan)
        """
        try:
            file_ext = os.path.splitext(filename)[1].lower() or '.jpg'
            timestamp = int(time.time())
            unique_filename = f"scan_{timestamp}{file_ext}"

            # Buat folder per user atau guest
            if user_id:
                user_folder = os.path.join(UPLOADS_DIR, f"user_{user_id}")
                relative_prefix = f"/uploads/user_{user_id}"
            else:
                user_folder = os.path.join(UPLOADS_DIR, "guest")
                relative_prefix = "/uploads/guest"
            
            os.makedirs(user_folder, exist_ok=True)

            file_path = os.path.join(user_folder, unique_filename)

            with open(file_path, 'wb') as f:
                f.write(file_content)

            relative_path = f"{relative_prefix}/{unique_filename}"
            return unique_filename, relative_path, file_path
        except Exception as e:
            print(f"Error saving image: {e}")
            return None, None, None

    @staticmethod
    def detect_diseases(absolute_image_path: str) -> Tuple[List[DiseaseDetectionItem], Optional[str]]:
        """
        Detect diseases dari image menggunakan YOLO model.
        Returns:
            - list of DiseaseDetectionItem
            - annotated_image_relative_path (path gambar dgn bounding box) atau None
        """
        try:
            # Validate file exists
            if not os.path.exists(absolute_image_path):
                raise FileNotFoundError(f"Image file not found: {absolute_image_path}")

            # Validate file is readable
            if not os.access(absolute_image_path, os.R_OK):
                raise PermissionError(f"Cannot read image file: {absolute_image_path}")

            model = get_yolo_model()

            # Run inference
            results = model.predict(
                source=absolute_image_path,
                conf=YOLO_CONFIDENCE_THRESHOLD,
                verbose=False,
            )

            if not results or len(results) == 0:
                # Tidak ada deteksi → kembalikan Healthy
                return [DiseaseDetectionItem(
                    disease_name="Healthy",
                    category="Healthy",
                    confidence=1.0,
                    recommendations="Tanaman terlihat sehat. Lanjutkan perawatan rutin | Pastikan nutrisi tanaman terpenuhi | Jaga pengelolaan air sawah yang baik",
                    severity="None",
                    bbox=None,
                )], None

            result = results[0]
            boxes = result.boxes

            if boxes is None or len(boxes) == 0:
                # Tidak ada objek terdeteksi → Healthy
                return [DiseaseDetectionItem(
                    disease_name="Healthy",
                    category="Healthy",
                    confidence=1.0,
                    recommendations="Tanaman terlihat sehat. Lanjutkan perawatan rutin | Pastikan nutrisi tanaman terpenuhi | Jaga pengelolaan air sawah yang baik",
                    severity="None",
                    bbox=None,
                )], None

            # ── Kumpulkan semua deteksi per box ──
            raw_detections = {}  # { disease_name: { best_conf, category, bboxes[] } }
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                # Langsung pakai model.names agar SELALU cocok dengan bounding box label
                disease_name = model.names.get(cls_id, f"Unknown-{cls_id}")

                if disease_name not in raw_detections:
                    raw_detections[disease_name] = {
                        "best_conf": conf,
                        "bboxes": [[round(c, 2) for c in xyxy]],
                        "count": 1,
                    }
                else:
                    entry = raw_detections[disease_name]
                    entry["bboxes"].append([round(c, 2) for c in xyxy])
                    entry["count"] += 1
                    if conf > entry["best_conf"]:
                        entry["best_conf"] = conf

            # ── Group: 1 penyakit = 1 DiseaseDetectionItem (confidence tertinggi) ──
            diseases = []
            for disease_name, info in raw_detections.items():
                conf = info["best_conf"]
                category = CLASS_CATEGORIES.get(disease_name, "Disease")
                severity = get_severity(conf)

                # Normalisasi nama penyakit agar cocok dengan CLASS_RECOMMENDATIONS
                normalized_name = disease_name.replace("_", " ")
                recs = CLASS_RECOMMENDATIONS.get(normalized_name, ["Monitor tanaman secara rutin"])
                rec_text = " | ".join(recs)

                diseases.append(DiseaseDetectionItem(
                    disease_name=disease_name,
                    category=category,
                    confidence=round(conf, 4),
                    recommendations=rec_text,
                    severity=severity,
                    bbox=info["bboxes"][0],  # bbox confidence tertinggi (pertama disimpan)
                ))

            # ── Generate annotated image (gambar + bounding box) ──
            annotated_rel_path = DetectionService._save_annotated_image(
                absolute_image_path, result
            )

            return diseases, annotated_rel_path
        except Exception as e:
            print(f"Error during YOLO detection: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise agar endpoint bisa handle error dengan proper HTTP response
            raise Exception(f"YOLO detection failed: {str(e)}")

    @staticmethod
    def _save_annotated_image(original_path: str, result) -> Optional[str]:
        """
        Gambar bounding box di atas image asli dan simpan sebagai file baru.
        Return relative path untuk serving via API.
        """
        try:
            annotated_frame = result.plot()  # numpy array BGR dengan boxes

            # Buat filename annotated
            dir_name = os.path.dirname(original_path)
            base_name = os.path.splitext(os.path.basename(original_path))[0]
            annotated_filename = f"{base_name}_annotated.jpg"
            annotated_abs_path = os.path.join(dir_name, annotated_filename)

            cv2.imwrite(annotated_abs_path, annotated_frame)

            # Extract relative path dari UPLOADS_DIR
            # original_path = .../app/uploads/user_1/scan_123.jpg
            # relative = /uploads/user_X/scan_123_annotated.jpg
            uploads_parent = os.path.dirname(UPLOADS_DIR)
            rel = os.path.relpath(annotated_abs_path, uploads_parent).replace("\\", "/")
            return f"/{rel}"
        except Exception as e:
            print(f"Warning: could not save annotated image: {e}")
            return None

    @staticmethod
    def get_recommendations(disease_name: str) -> List[str]:
        """Get treatment recommendations based on disease"""
        normalized_name = disease_name.replace("_", " ")
        return CLASS_RECOMMENDATIONS.get(normalized_name, ["Monitor tanaman secara rutin"])

    @staticmethod
    def save_detection_to_db(
        db: Session,
        user_id: int,
        image_filename: str,
        image_path: str,
        diseases: List[DiseaseDetectionItem],
        annotated_image_path: str = None,
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
            annotated_image_path=annotated_image_path,
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
                bbox=disease.bbox,
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
