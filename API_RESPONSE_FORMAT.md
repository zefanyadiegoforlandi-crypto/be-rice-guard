"""
Frontend API Response Format untuk Multiple Diseases

Ini adalah format response yang frontend akan terima setelah scan.
"""

# ==================== SINGLE DISEASE (SEBELUMNYA) ====================

RESPONSE_OLD_FORMAT = {
    "id": 1,
    "disease": "Leaf Blast",
    "category": "Fungal",
    "confidence": 0.92,
    "recommendations": "Spray fungicide...",
    "timestamp": "2026-02-07T10:30:00",
    "image_path": "/uploads/user_1/scan.jpg"
}


# ==================== MULTIPLE DISEASES (BARU, SESUAI REQUIREMENT) ====================

RESPONSE_NEW_FORMAT = {
    "id": 1,
    "image_filename": "scan_1707216000.jpg",
    "image_path": "/uploads/user_1/scan_1707216000.jpg",
    "disease_count": 2,  # Jumlah penyakit terdeteksi
    "diseases": [
        {
            "disease_name": "Leaf Blast",
            "category": "Fungal Disease",
            "confidence": 0.92,
            "recommendations": "Spray fungicide containing tricyclazole, Bayleton, or Tilt. Repeat application every 10-14 days.",
            "severity": "High"
        },
        {
            "disease_name": "Brown Spot",
            "category": "Fungal Disease",
            "confidence": 0.78,
            "recommendations": "Apply carbendazim, mancozeb, or propiconazole. Improve field drainage and air circulation.",
            "severity": "Medium"
        }
    ],
    "created_at": "2026-02-07T10:30:00Z"
}


# ==================== HEALTHY PLANT (1 DISEASE DENGAN CONFIDENCE 0.99) ====================

RESPONSE_HEALTHY = {
    "id": 2,
    "image_filename": "scan_1707216100.jpg",
    "image_path": "/uploads/user_1/scan_1707216100.jpg",
    "disease_count": 1,
    "diseases": [
        {
            "disease_name": "Healthy",
            "category": "No Disease",
            "confidence": 0.99,
            "recommendations": "Plant is healthy! Continue regular maintenance and monitoring.",
            "severity": "None"
        }
    ],
    "created_at": "2026-02-07T10:35:00Z"
}


# ==================== PEST + DISEASE ====================

RESPONSE_PEST_AND_DISEASE = {
    "id": 3,
    "image_filename": "scan_1707216200.jpg",
    "image_path": "/uploads/user_1/scan_1707216200.jpg",
    "disease_count": 2,
    "diseases": [
        {
            "disease_name": "Rice Brown Planthopper",
            "category": "Pest",
            "confidence": 0.95,
            "recommendations": "Use insecticides like carbofuran, imidacloprid, or thiamethoxam. Check water level.",
            "severity": "High"
        },
        {
            "disease_name": "Leaf Scald",
            "category": "Bacterial Disease",
            "confidence": 0.65,
            "recommendations": "No cure once infected. Use resistant varieties. Practice sanitation.",
            "severity": "High"
        }
    ],
    "created_at": "2026-02-07T10:40:00Z"
}


# ==================== HISTORY RESPONSE ====================

RESPONSE_HISTORY = {
    "total": 3,
    "items": [
        {
            "id": 1,
            "image_filename": "scan_1707216000.jpg",
            "image_path": "/uploads/user_1/scan_1707216000.jpg",
            "disease_count": 2,
            "diseases": [
                {
                    "disease_name": "Leaf Blast",
                    "category": "Fungal Disease",
                    "confidence": 0.92,
                    "recommendations": "...",
                    "severity": "High"
                },
                {
                    "disease_name": "Brown Spot",
                    "category": "Fungal Disease",
                    "confidence": 0.78,
                    "recommendations": "...",
                    "severity": "Medium"
                }
            ],
            "created_at": "2026-02-07T10:30:00Z"
        },
        # ... more items
    ]
}
