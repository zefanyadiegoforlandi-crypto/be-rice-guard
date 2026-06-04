import os
from dotenv import load_dotenv

load_dotenv()

def _parse_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(',') if item.strip()]

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
ACCESS_TOKEN_EXPIRE_MINUTES = 180

# ===================== FILE PATHS (Legacy JSON support) =====================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
DETECTIONS_FILE = os.path.join(DATA_DIR, "detections.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# ===================== CORS CONFIGURATION =====================
_default_cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
]

CORS_ORIGINS = _parse_env_list(os.getenv("CORS_ORIGINS")) or _default_cors_origins

# ===================== AI MODEL CONFIGURATION =====================
ML_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml_models")
YOLO_MODEL_PATH = os.path.join(ML_MODELS_DIR, "best.pt")
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.25"))

# Category per class (semua penyakit daun padi)
CLASS_CATEGORIES = {
    "Bacterial Leaf Blight": "Disease",
    "Rice Blast": "Disease",
    "Brown Spot": "Disease",
}

# Recommendations per class
CLASS_RECOMMENDATIONS = {
    "Bacterial Leaf Blight": [
        "Gunakan varietas tahan penyakit (contoh: IR64, Ciherang)",
        "Potong dan buang daun yang terinfeksi",
        "Kurangi pemupukan nitrogen berlebihan",
        "Perbaiki drainase sawah untuk mengurangi kelembapan",
        "Aplikasikan bakterisida berbahan dasar tembaga",
    ],
    "Rice Blast": [
        "Gunakan fungisida (Tricyclazole, Isoprothiolane)",
        "Tanam varietas tahan blast",
        "Kurangi pemupukan nitrogen berlebihan",
        "Jaga jarak tanam yang optimal untuk sirkulasi udara",
        "Lakukan rotasi tanaman untuk memutus siklus penyakit",
    ],
    "Brown Spot": [
        "Aplikasikan fungisida (Mancozeb, Propiconazole)",
        "Gunakan varietas tahan penyakit",
        "Tingkatkan pemupukan kalium dan fosfor",
        "Perbaiki drainase dan pengelolaan air sawah",
        "Bersihkan sisa tanaman setelah panen",
    ],
}

# Severity thresholds based on confidence
def get_severity(confidence: float) -> str:
    if confidence >= 0.85:
        return "High"
    elif confidence >= 0.60:
        return "Medium"
    else:
        return "Low"

