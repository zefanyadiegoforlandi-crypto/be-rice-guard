# MySQL Database Setup untuk Rice Detection Backend
## Dengan Support Multiple Diseases per Scan ✨

## ✓ Files Created

### 1. Database Configuration Files
- **`backend/migrations/001_initial_schema.sql`** - SQL migration file dengan DDL untuk 4 tables:
  - `users` - Menyimpan data user
  - `detections` - Menyimpan history scan hasil deteksi (metadata: image, disease_count)
  - `detection_diseases` - **[BARU]** Menyimpan multiple diseases per scan (bisa 1-N per scan)
  - `image_metadata` - Optional metadata gambar (size, dimensions, dll)

- **`backend/app/models/database.py`** - SQLAlchemy ORM models untuk semua tables
  - User model
  - Detection model  
  - **DetectionDisease model** [BARU] - untuk menyimpan multiple diseases
  - ImageMetadata model

- **`backend/app/models/database_init.py`** - Database connection dan session management
  - Engine setup dengan MySQL
  - SessionLocal factory
  - Helper functions: init_db(), drop_db(), get_db()

- **`backend/.env.example`** - Environment variables template untuk MySQL config

### 2. Updated Files
- **`backend/requirements.txt`** - Added:
  - `sqlalchemy==2.0.23` - ORM
  - `mysql-connector-python==8.2.0` - MySQL driver
  - `alembic==1.13.1` - Migration tool

- **`backend/app/models/schemas.py`** - Updated Pydantic schemas:
  - **DiseaseDetectionItem** [BARU] - single disease object
  - DetectionResponse dengan `diseases: List[DiseaseDetectionItem]`
  - DetectionHistoryResponse untuk history dengan multiple diseases
  - ImageMetadataResponse
  - Config: `from_attributes = True` untuk SQLAlchemy

- **`backend/app/config.py`** - Added database config:
  - DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
  - SQLALCHEMY_DATABASE_URL
  - USE_DATABASE flag (untuk backward compatibility)

- **`backend/app/main.py`** - Updated startup event:
  - Auto initialize database tables on startup
  - Graceful fallback jika database error

### 3. Documentation & Examples
- **`backend/DATABASE_SETUP.md`** - Complete setup guide:
  - MySQL installation
  - Database creation
  - .env configuration
  - Migration steps
  - Schema overview
  - Image storage location
  - Troubleshooting

## 🔄 Database Schema

### users table
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email)
);
```

### detections table (HISTORY SCAN)
```sql
CREATE TABLE detections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_filename VARCHAR(255) NOT NULL,
    image_path VARCHAR(500) NOT NULL,
    disease VARCHAR(255),
    category VARCHAR(255),
    confidence FLOAT,
    recommendations LONGTEXT,
    analysis_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

### image_metadata table
```sql
CREATE TABLE image_metadata (
    id INT PRIMARY KEY AUTO_INCREMENT,
    detection_id INT NOT NULL,
    original_filename VARCHAR(255),
    file_size INT,
    mime_type VARCHAR(100),
    width INT,
    height INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (detection_id) REFERENCES detections(id),
    INDEX idx_detection_id (detection_id)
);
```

## 📁 Image Storage

Gambar disimpan di: `backend/app/uploads/`

Format: `user_{user_id}/scan_{timestamp}.jpg`

Contoh:
```
backend/app/uploads/user_1/scan_1707216000.jpg
backend/app/uploads/user_2/scan_1707216100.jpg
```

Di database disimpan:
- `image_filename`: `scan_1707216000.jpg`
- `image_path`: `/uploads/user_1/scan_1707216000.jpg`

## 🚀 Quick Start

### 1. Install MySQL
Download dari: https://dev.mysql.com/downloads/mysql/

### 2. Create Database
```bash
mysql -u root -p
CREATE DATABASE rice_detection_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit
```

### 3. Setup Backend
```bash
cd backend

# Copy env file
cp .env.example .env

# Edit .env with your MySQL credentials
# DB_USER=root
# DB_PASSWORD=your_password
# DB_HOST=localhost
# DB_PORT=3306
# DB_NAME=rice_detection_db
# USE_DATABASE=True

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.models.database_init import init_db; init_db()"

# Start server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Verify Tables
```bash
mysql -u root -p rice_detection_db
SHOW TABLES;
DESCRIBE users;
DESCRIBE detections;
DESCRIBE image_metadata;
```

## 📝 Next Steps

Setelah database siap, untuk integration dengan services:

### 1. Update `auth_service.py`
- Change dari JSON file ke database insert/select
- Hash password dengan bcrypt
- Generate JWT token

### 2. Update `detection_service.py`
- Save gambar ke `uploads/user_{user_id}/scan_{timestamp}.jpg`
- Insert detection record ke database
- Save image metadata (optional)

### 3. Create History Endpoint
- GET `/api/detection/history` - List semua scan user
- GET `/api/detection/{id}` - Detail single scan
- DELETE `/api/detection/{id}` - Hapus scan

### 4. Update Frontend
- Already ready untuk consume API
- Hanya perlu test end-to-end

## ✅ Compatibility

**Backward Compatible:**
- `USE_DATABASE = False` → masih pakai JSON files lama
- `USE_DATABASE = True` → pakai MySQL

Default: `USE_DATABASE = True`

## 🔧 Troubleshooting

### "Can't connect to MySQL"
- Pastikan MySQL running
- Cek credentials di .env

### "rice_detection_db doesn't exist"
- Run `CREATE DATABASE rice_detection_db;`

### "Unknown table"
- Run `python -c "from app.models.database_init import init_db; init_db()"`

## 📚 Files Summary

```
backend/
├── migrations/
│   └── 001_initial_schema.sql        [NEW] SQL DDL
├── app/
│   ├── models/
│   │   ├── database.py               [NEW] SQLAlchemy models
│   │   ├── database_init.py          [NEW] Connection & session
│   │   └── schemas.py                [UPDATED] Pydantic schemas
│   ├── config.py                     [UPDATED] DB config
│   └── main.py                       [UPDATED] DB init on startup
├── .env.example                      [NEW] Env template
├── DATABASE_SETUP.md                 [NEW] Setup guide
└── requirements.txt                  [UPDATED] Added SQLAlchemy
```

---

**Status**: ✅ Ready for implementation
**Database**: MySQL 8.0+
**ORM**: SQLAlchemy 2.0
**Migration**: 001_initial_schema.sql
