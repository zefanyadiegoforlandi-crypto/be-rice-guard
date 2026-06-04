# Database Migration Best Practice Guide

## Overview

Backend ini sudah di-setup dengan sistem migration yang best practice menggunakan:
- **SQL migrations** (untuk historical reference dan manual migrations)
- **Alembic** (untuk auto-generate migrations dari model changes)
- **Auto-runner** (untuk jalankan semua migrations otomatis)

---

## Setup Awal (WAJIB DIJALANKAN 1 KALI)

```bash
cd backend

# 1. Install requirements
pip install -r requirements.txt

# 2. Jalankan auto-migration runner (ini akan run semua SQL migrations + init models)
python run_migrations.py

# Sekarang database sudah siap dengan semua kolom termasuk 'role'
```

---

## How to Use (Going Forward)

### **Skenario 1: Ada perubahan di model** (ubah `database.py`)

**Contoh: tambah kolom baru di User model**

1. Edit `app/models/database.py`:
```python
class User(Base):
    # ...existing code...
    status = Column(String(50), default='active', nullable=False)  # ← tambah ini
```

2. Generate migration otomatis:
```bash
alembic revision --autogenerate -m "Add status column to users"
```

3. Review generated migration di `alembic/versions/xxx_add_status_column_to_users.py`

4. Jalankan migration:
```bash
alembic upgrade head
```

---

### **Skenario 2: Manual SQL migration** (untuk query kompleks)

1. Buat file di `migrations/`:
```bash
# Nomor harus sequence, contoh: jika last adalah 004, buat 005_xxx.sql
migrations/005_add_invoice_table.sql
```

2. Tulis SQL query:
```sql
-- Migration: Add invoice table
CREATE TABLE invoices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    amount DECIMAL(10,2),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

3. Jalankan runner:
```bash
python run_migrations.py
```

---

### **Skenario 3: Check current migration status**

```bash
# Check which migrations sudah dijalankan
alembic current

# Check migration history
alembic history
```

---

## Important Notes

### ✅ DO's:
- ✅ Always run `python run_migrations.py` sebelum start backend
- ✅ Edit model → auto-generate migration dengan Alembic
- ✅ Commit migration files ke git
- ✅ Review migration files sebelum jalankan

### ❌ DON'Ts:
- ❌ Jangan edit `alembic/versions/*.py` manual (auto-generated)
- ❌ Jangan jalankan multiple migrations dalam 1 transaksi
- ❌ Jangan delete old migration files
- ❌ Jangan edit nomor migration files

---

## Troubleshooting

**Problem: "Unknown column 'X' in 'field list'"**
- Solution: Jalankan `python run_migrations.py` untuk update database schema

**Problem: Migration conflict**
- Check: `alembic heads`
- Resolve: Manual merge di `alembic/versions/`

**Problem: Need to rollback**
```bash
alembic downgrade -1  # Rollback 1 migration
alembic downgrade base  # Rollback semua
```

---

## File Structure

```
backend/
├── migrations/              ← Manual SQL migrations (legacy)
│   ├── 001_initial_schema.sql
│   ├── 002_add_bbox_and_annotated_image.sql
│   ├── 003_add_role_to_users.sql
│   └── 004_make_user_id_nullable.sql
│
├── alembic/                 ← Alembic migrations (best practice)
│   ├── env.py
│   ├── script.py.mako
│   └── versions/            ← Auto-generated migrations go here
│
├── alembic.ini              ← Alembic configuration
├── run_migrations.py        ← Auto-runner script
├── app/
│   └── models/
│       └── database.py      ← Define models here
└── init_db.py               ← Old way (deprecated, use run_migrations.py)
```

---

## Commands Reference

```bash
# Initialize database (first time only)
python run_migrations.py

# Create migration from model changes
alembic revision --autogenerate -m "Descriptive message"

# Apply all pending migrations
alembic upgrade head

# Rollback 1 migration
alembic downgrade -1

# Show current migration
alembic current

# Show migration history
alembic history

# Check if database is up-to-date
alembic current -v

# Create empty migration (untuk manual SQL)
alembic revision -m "Manual migration name"
```

---

## Best Practice Summary

```
Model change → Auto-generate migration → Review → Apply → Commit
```

This ensures:
- ✨ Clean schema history
- 🔄 Easy rollback
- 👥 Team collaboration
- 🔍 Audit trail
