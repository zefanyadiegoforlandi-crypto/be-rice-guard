import os
from dotenv import load_dotenv

load_dotenv()

# ===================== DATABASE CONFIGURATION =====================
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "rice_detection_db")

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Use MySQL (set to True) or JSON files (set to False)
USE_DATABASE = os.getenv("USE_DATABASE", "True").lower() == "true"

# ===================== JWT CONFIGURATION =====================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ===================== FILE PATHS (Legacy JSON support) =====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DETECTIONS_FILE = os.path.join(DATA_DIR, "detections.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ===================== CORS CONFIGURATION =====================
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
]

# ===================== AI MODEL DETECTION - MOCK VALUES =====================
DISEASES = ["Leaf Blast", "Brown Spot", "Bacterial Leaf Blight", "Healthy"]
PESTS = ["Rice Brown Planthopper", "Rice Leafhopper", "Rice Case Worm", "No Pest"]
COMMON_ISSUES = [
    {"name": "Leaf Blast", "type": "disease", "confidence": 0.92},
    {"name": "Brown Spot", "type": "disease", "confidence": 0.87},
    {"name": "Bacterial Leaf Blight", "type": "disease", "confidence": 0.78},
    {"name": "Rice Brown Planthopper", "type": "pest", "confidence": 0.95},
    {"name": "Rice Leafhopper", "type": "pest", "confidence": 0.88},
    {"name": "Healthy", "type": "healthy", "confidence": 0.99},
]

