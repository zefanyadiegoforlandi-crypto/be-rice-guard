-- Migration: 003_add_role_to_users
-- Description: Add role column to users table for admin and user roles
-- Created: 2026-04-21

-- Add role column if it doesn't exist
ALTER TABLE users
ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' NOT NULL,
ADD INDEX IF NOT EXISTS idx_role (role);

-- Set existing users as 'user' role (in case table already has data)
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';
