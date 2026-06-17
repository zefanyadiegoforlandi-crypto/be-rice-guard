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
    "https://sekarpadi.online",
    "https://www.sekarpadi.online",
    "https://fe-rice-guard.vercel.app/",

]

CORS_ORIGINS = _parse_env_list(os.getenv("CORS_ORIGINS")) or _default_cors_origins

# ===================== AI MODEL CONFIGURATION =====================
ML_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "ml_models")
YOLO_MODEL_PATH = os.path.join(ML_MODELS_DIR, "best.pt")
YOLO_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.25"))

# Category per class (semua penyakit daun padi)
CLASS_CATEGORIES = {
    "Bacterial Blight": "Disease",
    "Rice Blast": "Disease",
    "Brown Spot": "Disease",
}

# Recommendations per class
CLASS_RECOMMENDATIONS = {
    "Bacterial Blight": [
        "Menanam varietas yang tahan terhadap penyakit, terutama varietas Code dan Angke pada wilayah endemis.",
        "PMenghindari pemotongan bagian ujung bibit sebelum dilakukan penanaman.",
        "Mengatur jarak tanam agar tidak terlalu rapat, salah satunya dengan menerapkan sistem tanam jajar legowo.",
        "Menerapkan pengairan berselang (intermittent irrigation) serta menghindari kondisi lahan yang tergenang secara terus-menerus.",
        "Melakukan pemupukan secara berimbang dan menghindari penggunaan pupuk nitrogen (N) dalam jumlah berlebihan.",
        "Melakukan penyemprotan bakterisida apabila intensitas serangan penyakit telah melebihi 20%.",
    ],
    "Rice Blast": [
        "Menanam varietas yang memiliki ketahanan terhadap penyakit blast secara bergantian untuk mengantisipasi perubahan ras cendawan yang berlangsung relatif cepat. Beberapa varietas yang diketahui masih cukup tahan antara lain Limboto, Situ Patenggang, dan Batutegi.",
        "Pupuk nitrogen (N) sebaiknya diberikan sesuai kebutuhan tanaman. Aplikasi urea pada kisaran 100–150 kg/ha dilaporkan lebih efektif dalam menekan keparahan penyakit blast, sedangkan peningkatan dosis di atas kisaran tersebut tidak menunjukkan kecenderungan yang sama dalam pengurangan serangan penyakit.",
        "Mengatur waktu tanam dengan tepat sehingga fase pembungaan tidak terjadi pada kondisi yang memiliki embun berlebihan.",
        "Melakukan perlakuan benih (seed treatment) sejak awal karena penyakit blast dapat ditularkan melalui benih. Perlakuan ini dapat dilakukan menggunakan fungisida sistemik agar pengendalian lebih efektif.",
        "Mengaplikasikan fungisida berbahan aktif tiofanat, fosdifen, atau kasugamisin apabila diperlukan.",
    ],
    "Brown Spot": [
        "Menanam varietas yang tahan terhadap penyakit bercak coklat, seperti Ciherang dan Membrano.",
        "Menggunakan jarak tanam yang tidak terlalu rapat, misalnya dengan menerapkan sistem tanam legowo.",
        "Melakukan pemupukan secara berimbang sesuai kebutuhan tanaman.",
        "Mengaplikasikan fungisida pada daun padi yang mengandung bahan aktif azoksistrobin, belerang, difenokonazol, tebukonazol, karbendazim, metil tiofanat, atau klorotalonil.",
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

