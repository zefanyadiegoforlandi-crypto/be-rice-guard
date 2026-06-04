# 🌾 Rice Guard — Backend API

REST API untuk platform deteksi penyakit dan hama tanaman padi berbasis AI.

## Tech Stack

| Teknologi | Versi | Fungsi |
|-----------|-------|--------|
| **FastAPI** | 0.104 | Web framework |
| **Uvicorn** | 0.24 | ASGI server |
| **SQLAlchemy** | 2.0 | ORM database |
| **MySQL** | 8.x | Database utama |
| **JWT (python-jose)** | 3.3 | Autentikasi token |
| **Passlib + bcrypt** | — | Hashing password |
| **Pillow** | 10.1 | Pemrosesan gambar |

---

## Struktur Folder

```
backend/
├── app/
│   ├── main.py              # Entry point FastAPI
│   ├── config.py             # Konfigurasi (DB, JWT, CORS)
│   ├── models/
│   │   ├── database.py       # SQLAlchemy engine & session
│   │   ├── database_init.py  # Inisialisasi tabel
│   │   └── schemas.py        # Pydantic schemas (request/response)
│   ├── routes/
│   │   ├── auth.py           # Endpoint autentikasi
│   │   ├── detection.py      # Endpoint deteksi & riwayat
│   │   └── health.py         # Health check
│   ├── services/
│   │   ├── auth_service.py   # Logika bisnis auth
│   │   └── detection_service.py # Logika bisnis deteksi AI
│   ├── utils/
│   │   ├── file_handler.py   # Upload & manajemen file
│   │   └── security.py       # JWT & password utilities
│   ├── uploads/              # Folder penyimpanan gambar
│   └── data/                 # Legacy JSON storage
├── migrations/
│   └── 001_initial_schema.sql
├── requirements.txt
└── README.md
```

---

## Instalasi & Setup

### 1. Buat virtual environment

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi environment

Buat file `.env` di folder `backend/`:

```env
# Database
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=rice_detection_db

# JWT
SECRET_KEY=your-secret-key-change-this-in-production

# Mode database (True = MySQL, False = JSON file)
USE_DATABASE=True
```

### 4. Setup database

```sql
CREATE DATABASE rice_detection_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Jalankan migration:

```bash
mysql -u root -p rice_detection_db < migrations/001_initial_schema.sql
```

### 5. Jalankan server

```bash
uvicorn app.main:app --reload --port 8000
```

Server berjalan di `http://localhost:8000`

---

## API Endpoints

### Health Check

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `GET` | `/` | Root info |
| `GET` | `/health` | Status server |

### Autentikasi (`/auth`)

| Method | Endpoint | Deskripsi | Auth |
|--------|----------|-----------|------|
| `POST` | `/auth/register` | Daftar akun baru | ❌ |
| `POST` | `/auth/login` | Login & dapatkan token | ❌ |
| `GET` | `/auth/me` | Profil user saat ini | ✅ |
| `PUT` | `/auth/update-name` | Ubah nama user | ✅ |

### Deteksi (`/detection`)

| Method | Endpoint | Deskripsi | Auth |
|--------|----------|-----------|------|
| `POST` | `/detection/scan` | Upload foto & analisis AI | ✅ |
| `GET` | `/detection/history` | Riwayat semua scan | ✅ |
| `GET` | `/detection/stats` | Statistik dashboard | ✅ |
| `PATCH` | `/detection/history/{id}/rename` | Rename label gambar | ✅ |
| `DELETE` | `/detection/history/{id}` | Hapus 1 deteksi | ✅ |
| `DELETE` | `/detection/history` | Hapus semua riwayat | ✅ |

---

## Autentikasi

Menggunakan **JWT Bearer Token**. Sesi berlaku **3 jam**.

```
Authorization: Bearer <token>
```

Token didapat dari response `/auth/login` atau `/auth/register`.

---

## Database Schema

### `users`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INT (PK) | Auto increment |
| email | VARCHAR(255) | Unique, login identifier |
| name | VARCHAR(255) | Nama tampilan |
| password_hash | VARCHAR(255) | Bcrypt hash |
| created_at | TIMESTAMP | Waktu registrasi |

### `detections`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INT (PK) | Auto increment |
| user_id | INT (FK) | Referensi ke users |
| image_filename | VARCHAR(255) | Nama file tersimpan |
| image_path | VARCHAR(500) | Path file |
| disease_count | INT | Jumlah penyakit terdeteksi |
| created_at | TIMESTAMP | Waktu scan |

### `detection_diseases`
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INT (PK) | Auto increment |
| detection_id | INT (FK) | Referensi ke detections |
| disease_name | VARCHAR(255) | Nama penyakit/hama |
| category | VARCHAR(255) | `disease` / `pest` / `healthy` |
| confidence | FLOAT | Tingkat keyakinan (0.0–1.0) |
| recommendations | LONGTEXT | Saran penanganan |
| severity | VARCHAR(50) | `Low` / `Medium` / `High` |

> Satu scan dapat memiliki **multiple diseases** (relasi one-to-many).

---

## Contoh Request & Response

### Register

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "name": "Petani", "password": "password123"}'
```

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Petani"
  }
}
```

### Scan

```bash
curl -X POST http://localhost:8000/detection/scan \
  -H "Authorization: Bearer <token>" \
  -F "file=@photo.jpg" \
  -F "image_name=Sawah Blok A"
```

```json
{
  "id": 1,
  "image_name": "Sawah Blok A",
  "image_filename": "1707350400_photo.jpg",
  "image_path": "/uploads/user_1/1707350400_photo.jpg",
  "disease_count": 2,
  "diseases": [
    {
      "disease_name": "Leaf Blast",
      "category": "disease",
      "confidence": 0.92,
      "severity": "High",
      "recommendations": "Aplikasikan fungisida Tricyclazole..."
    },
    {
      "disease_name": "Rice Brown Planthopper",
      "category": "pest",
      "confidence": 0.85,
      "severity": "Medium",
      "recommendations": "Gunakan insektisida..."
    }
  ],
  "created_at": "2026-02-08T10:00:00"
}
```
