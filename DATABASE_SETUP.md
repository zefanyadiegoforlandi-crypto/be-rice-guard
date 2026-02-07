# Database Setup Guide untuk MySQL

## Step 1: Install MySQL Server
- Download dari: https://dev.mysql.com/downloads/mysql/
- Install MySQL Server and MySQL Workbench

## Step 2: Create Database

```sql
-- Login ke MySQL
mysql -u root -p

-- Create database
CREATE DATABASE rice_detection_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Verify
SHOW DATABASES;
```

## Step 3: Configure Backend

### Copy `.env.example` ke `.env`
```bash
cd backend
cp .env.example .env
```

### Edit `.env` dengan MySQL credentials
```env
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=rice_detection_db
```

## Step 4: Run Migration

### Option A: Using Python Script (AUTO CREATE TABLES)
```bash
cd backend
python -c "from app.models.database_init import init_db; init_db(); print('Database initialized!')"
```

### Option B: Using SQL Script (MANUAL)
```bash
mysql -u root -p rice_detection_db < migrations/001_initial_schema.sql
```

## Step 5: Verify Tables Created

```sql
mysql -u root -p rice_detection_db

-- Show tables
SHOW TABLES;

-- Show users table structure
DESCRIBE users;

-- Show detections table structure
DESCRIBE detections;

-- Show image_metadata table structure
DESCRIBE image_metadata;
```

## Step 6: Install Python Requirements

```bash
pip install -r requirements.txt
```

## Step 7: Start Backend Server

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Database Schema Overview

### users table
- `id`: Primary key
- `email`: Unique email
- `name`: User name
- `password_hash`: Hashed password
- `created_at`: Creation timestamp
- `updated_at`: Update timestamp

### detections table (SCANNING HISTORY)
- `id`: Primary key
- `user_id`: Foreign key to users
- `image_filename`: Stored filename (e.g., scan_1707216000.jpg)
- `image_path`: Full path to image (e.g., /uploads/user_1/scan_1707216000.jpg)
- `disease`: Disease name detected
- `category`: Disease category
- `confidence`: Confidence percentage
- `recommendations`: Treatment recommendations
- `analysis_data`: Extra JSON data
- `created_at`: Scan timestamp

### image_metadata table (OPTIONAL - IMAGE INFO)
- `id`: Primary key
- `detection_id`: Foreign key to detections
- `original_filename`: Original filename uploaded
- `file_size`: File size in bytes
- `mime_type`: Image MIME type
- `width`: Image width
- `height`: Image height
- `created_at`: Timestamp

## Image Storage

Images disimpan di: `backend/app/uploads/`

Naming convention: `user_{user_id}/scan_{timestamp}.jpg`

Contoh:
- `backend/app/uploads/user_1/scan_1707216000.jpg`
- `backend/app/uploads/user_2/scan_1707216100.jpg`

## Troubleshooting

### Error: "Can't connect to MySQL server"
- Pastikan MySQL server running
- Cek DB_HOST dan DB_PORT di .env
- Cek DB_USER dan DB_PASSWORD

### Error: "Database rice_detection_db doesn't exist"
- Buat database terlebih dahulu dengan SQL CREATE DATABASE

### Error: "Unknown table"
- Jalankan migration untuk buat tables

## Next Steps

Setelah setup database:
1. Update auth service untuk simpan ke DB
2. Update detection service untuk simpan ke DB dan file
3. Update history endpoint untuk read dari DB
4. Test end-to-end scanning dengan database
