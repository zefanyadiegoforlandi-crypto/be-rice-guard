-- Migration: 001_initial_schema
-- Description: Create initial database schema for rice detection app with multiple disease support
-- Created: 2026-02-07

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create detections table (history scan hasil deteksi)
CREATE TABLE IF NOT EXISTS detections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    disease_count INT DEFAULT 0,
    analysis_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create detection_diseases table (BARU - menyimpan multiple diseases per scan)
-- 1 scan bisa memiliki 2+ penyakit
CREATE TABLE IF NOT EXISTS detection_diseases (
    id INT PRIMARY KEY AUTO_INCREMENT,
    detection_id INT NOT NULL,
    disease_name VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    confidence FLOAT NOT NULL,
    recommendations LONGTEXT,
    severity VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE,
    INDEX idx_detection_id (detection_id),
    INDEX idx_disease_name (disease_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create image metadata table (optional, untuk tracking)
CREATE TABLE IF NOT EXISTS image_metadata (
    id INT PRIMARY KEY AUTO_INCREMENT,
    detection_id INT NOT NULL,
    original_filename VARCHAR(255),
    file_size INT,
    mime_type VARCHAR(100),
    width INT,
    height INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id) ON DELETE CASCADE,
    INDEX idx_detection_id (detection_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
