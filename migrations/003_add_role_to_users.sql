-- Migration: 003_add_role_to_users
-- Description: Add role column to users table for admin and user roles
-- Created: 2026-04-21

-- Set existing users as 'user' role (in case table already has data)
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';
