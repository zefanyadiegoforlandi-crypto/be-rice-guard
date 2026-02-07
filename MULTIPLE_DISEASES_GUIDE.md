# Multiple Diseases Support - Quick Guide

## 🎯 Requirement
Dalam 1 foto scan tanaman padi, bisa terdapat **2+ penyakit**, bukan hanya 1 penyakit saja.

**Yang harus di-return:**
- Semua penyakit yang terdeteksi
- Keyakinan (confidence) masing-masing
- Rekomendasi treatment untuk setiap penyakit
- Severity level

## 📊 Architecture

### Database Schema
```
detections table (1 scan) 
    ↓
detection_diseases table (1-N diseases per scan)
    ├── Disease 1: Leaf Blast (92% confidence)
    ├── Disease 2: Brown Spot (78% confidence)
    └── Disease 3: (if any)
```

**Key point:** 1 foto (Detection) bisa punya banyak DetectionDisease records.

### Old vs New

**OLD:**
```json
{
    "disease": "Leaf Blast",
    "confidence": 0.92,
    "recommendations": "..."
}
```

**NEW (Multiple):**
```json
{
    "disease_count": 2,
    "diseases": [
        {
            "disease_name": "Leaf Blast",
            "confidence": 0.92,
            "recommendations": "..."
        },
        {
            "disease_name": "Brown Spot",
            "confidence": 0.78,
            "recommendations": "..."
        }
    ]
}
```

## 📁 Files Updated

### Database
- `migrations/001_initial_schema.sql` - Added `detection_diseases` table
- `app/models/database.py` - Added `DetectionDisease` model dengan relationship

### API Models
- `app/models/schemas.py` - Added `DiseaseDetectionItem`, updated `DetectionResponse`

### Documentation
- `DETECTION_SERVICE_EXAMPLE.md` - How to implement
- `API_RESPONSE_FORMAT.md` - Response examples

## 🔧 Implementation Overview

### 1. AI Model Output (Example)
```python
# AI model returns multiple diseases
diseases = [
    DiseaseDetectionItem(
        disease_name="Leaf Blast",
        category="Fungal",
        confidence=0.92,
        recommendations="Spray fungicide..."
    ),
    DiseaseDetectionItem(
        disease_name="Brown Spot",
        category="Fungal",
        confidence=0.78,
        recommendations="Apply carbendazim..."
    )
]
```

### 2. Database Save
```python
# Create 1 Detection record
detection = Detection(
    user_id=user_id,
    image_filename="scan_1707216000.jpg",
    disease_count=2  # Number of diseases
)

# Create 2 DetectionDisease records
for disease in diseases:
    DetectionDisease(
        detection_id=detection.id,
        disease_name=disease.disease_name,
        confidence=disease.confidence,
        ...
    )
```

### 3. API Response
```python
# SQLAlchemy relationship auto-joins
{
    "id": 1,
    "disease_count": 2,
    "diseases": [
        # Auto-loaded dari detection_diseases
        {"disease_name": "Leaf Blast", ...},
        {"disease_name": "Brown Spot", ...}
    ]
}
```

## ✅ Files Breakdown

```
backend/
├── migrations/
│   └── 001_initial_schema.sql
│       └── UPDATED: detection_diseases table added
│
├── app/models/
│   ├── database.py
│   │   └── UPDATED: DetectionDisease + relationship
│   │
│   └── schemas.py
│       ├── NEW: DiseaseDetectionItem
│       └── UPDATED: DetectionResponse with diseases list
│
├── DETECTION_SERVICE_EXAMPLE.md [NEW]
│   └── Code examples untuk implementasi
│
└── API_RESPONSE_FORMAT.md [NEW]
    └── JSON response examples
```

## 🚀 Next Steps

1. **Setup MySQL & Create Database**
   ```bash
   mysql -u root -p
   CREATE DATABASE rice_detection_db;
   ```

2. **Initialize Database**
   ```bash
   cd backend
   python init_db.py
   ```

3. **Implement Services** (lihat DETECTION_SERVICE_EXAMPLE.md)
   - Update `detection_service.py` untuk save multiple diseases
   - Update detection endpoint untuk return diseases array
   - Update history endpoint untuk show multiple diseases

4. **Test End-to-End**
   - Upload image
   - Check database: 1 Detection + N DetectionDisease
   - Verify API response includes all diseases

## 📋 Detection Table Structure

```sql
-- 1 scan = 1 row
CREATE TABLE detections (
    id INT,                    -- Detection ID
    user_id INT,              -- User who scanned
    image_filename VARCHAR,    -- scan_1707216000.jpg
    disease_count INT,         -- How many diseases found
    ...
)

-- Multiple diseases = Multiple rows
CREATE TABLE detection_diseases (
    id INT,                    -- Record ID
    detection_id INT,         -- Links to detections
    disease_name VARCHAR,      -- "Leaf Blast" etc
    confidence FLOAT,          -- 0-1
    recommendations TEXT,      -- Treatment info
    ...
)
```

## 💡 Example Query

```python
# Get all detections dengan diseases untuk user
detections = db.query(Detection).filter(
    Detection.user_id == 1
).all()

# For each detection, access diseases via relationship
for detection in detections:
    print(f"Scan {detection.id}:")
    for disease in detection.diseases:  # Auto-loaded
        print(f"  - {disease.disease_name}: {disease.confidence}%")
```

**Output:**
```
Scan 1:
  - Leaf Blast: 92%
  - Brown Spot: 78%
Scan 2:
  - Healthy: 99%
```

---

**Ready untuk implement!** Lihat `DETECTION_SERVICE_EXAMPLE.md` untuk code details.
