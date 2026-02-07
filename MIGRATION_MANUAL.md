# Manual Migration Command untuk MySQL

## Jika ingin manual run SQL migration:

### Method 1: Langsung dengan MySQL CLI
```bash
mysql -u root -p rice_detection_db < migrations/001_initial_schema.sql
```

### Method 2: Dari Python
```bash
cd backend

# Run init script
python init_db.py

# Atau langsung
python -c "from app.models.database_init import init_db; init_db()"
```

### Method 3: Via FastAPI (Otomatis saat server start)
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Server akan otomatis:
1. Connect ke MySQL
2. Create all tables jika belum ada
3. Setup relationships dan indexes

## SQL Schema yang akan dibuat:

Lihat: `migrations/001_initial_schema.sql`

Tables:
- users (4 columns)
- detections (9 columns)
- image_metadata (7 columns)

Relationships:
- detections.user_id → users.id (CASCADE delete)
- image_metadata.detection_id → detections.id (CASCADE delete)

Indexes:
- users: idx_email
- detections: idx_user_id, idx_created_at
- image_metadata: idx_detection_id
