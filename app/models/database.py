from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='user', nullable=False)  # 'user' atau 'admin'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    detections = relationship("Detection", back_populates="user", cascade="all, delete-orphan")

    class Config:
        orm_mode = True


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # nullable untuk guest scan
    image_name = Column(String(255), nullable=True)  # Label/nama dari petani
    image_filename = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)
    annotated_image_path = Column(String(500), nullable=True)  # Path gambar dengan bounding box
    disease_count = Column(Integer, default=0)  # Jumlah penyakit terdeteksi
    analysis_data = Column(JSON, nullable=True)  # Extra data as JSON
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="detections")
    diseases = relationship("DetectionDisease", back_populates="detection", cascade="all, delete-orphan")
    image_metadata = relationship("ImageMetadata", back_populates="detection", cascade="all, delete-orphan")

    # Index
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_created_at', 'created_at'),
    )

    class Config:
        orm_mode = True


class DetectionDisease(Base):
    """Menyimpan multiple diseases per scan - 1 scan bisa punya 2+ penyakit"""
    __tablename__ = "detection_diseases"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False)
    disease_name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)  # e.g., "Disease"
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    recommendations = Column(Text, nullable=True)  # Treatment recommendations
    severity = Column(String(50), nullable=True)  # e.g., "Low", "Medium", "High"
    bbox = Column(JSON, nullable=True)  # Bounding box [x1, y1, x2, y2]
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    detection = relationship("Detection", back_populates="diseases")

    # Index
    __table_args__ = (
        Index('idx_detection_id', 'detection_id'),
        Index('idx_disease_name', 'disease_name'),
    )

    class Config:
        orm_mode = True


class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(Integer, ForeignKey("detections.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    detection = relationship("Detection", back_populates="image_metadata")

    # Index
    __table_args__ = (
        Index('idx_detection_id', 'detection_id'),
    )

    class Config:
        orm_mode = True
