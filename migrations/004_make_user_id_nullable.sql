-- Migration: Make user_id nullable untuk support guest scan
-- Date: 2026-04-20

ALTER TABLE detections MODIFY COLUMN user_id INT NULL;

-- Add index untuk user_id nullable jika belum ada
-- (index sudah ada di schema, so just making sure)
