"""
Initialize sample data for testing
Run this script untuk create sample users dan detections
"""

import json
import os
from app.config import USERS_FILE, DETECTIONS_FILE, DATA_DIR
from app.utils.security import hash_password

def create_sample_data():
    """Create sample users and detections for testing"""
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create sample users
    sample_users = {
        "users": {
            "demo@example.com": {
                "email": "demo@example.com",
                "name": "Demo User",
                "password": hash_password("demo123"),
                "created_at": "2026-02-01"
            },
            "farmer@example.com": {
                "email": "farmer@example.com",
                "name": "John Farmer",
                "password": hash_password("farmer123"),
                "created_at": "2026-02-01"
            }
        }
    }
    
    # Create sample detections
    sample_detections = {
        "demo@example.com": [
            {
                "id": "001",
                "disease": "Leaf Blast",
                "type": "disease",
                "confidence": 0.92,
                "recommendations": [
                    "Apply fungicide immediately",
                    "Increase field ventilation",
                    "Reduce nitrogen fertilizer"
                ],
                "timestamp": "2026-02-01T10:30:00",
                "image_path": "sample_1.jpg"
            },
            {
                "id": "002",
                "disease": "Healthy",
                "type": "healthy",
                "confidence": 0.98,
                "recommendations": [
                    "Continue regular monitoring",
                    "Maintain proper nutrition",
                    "Ensure good water management"
                ],
                "timestamp": "2026-02-01T11:45:00",
                "image_path": "sample_2.jpg"
            }
        ]
    }
    
    # Write to files
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sample_users, f, indent=2, ensure_ascii=False)
    print(f"✓ Created sample users at {USERS_FILE}")
    
    with open(DETECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sample_detections, f, indent=2, ensure_ascii=False)
    print(f"✓ Created sample detections at {DETECTIONS_FILE}")
    
    print("\nSample Credentials:")
    print("- Email: demo@example.com, Password: demo123")
    print("- Email: farmer@example.com, Password: farmer123")

if __name__ == "__main__":
    create_sample_data()
