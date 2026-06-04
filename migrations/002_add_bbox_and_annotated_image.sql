-- Migration: 002_add_bbox_and_annotated_image
-- Description: Add bounding box column to detection_diseases and annotated_image_path to detections
-- Created: 2026-02-11

-- Add annotated_image_path column to detections table
ALTER TABLE detections
    ADD COLUMN annotated_image_path VARCHAR(500) NULL AFTER image_path;

-- Add bbox JSON column to detection_diseases table
ALTER TABLE detection_diseases
    ADD COLUMN bbox JSON NULL AFTER severity;

-- Update image_name column if not exists (from previous migration)
ALTER TABLE detections
    ADD COLUMN image_name VARCHAR(255) NULL AFTER user_id;
