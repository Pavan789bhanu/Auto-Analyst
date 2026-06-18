import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
RESULTS_DIR = DATA_DIR / "results"
DB_PATH = DATA_DIR / "autoanalyst.db"

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "86400"))

USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "auto-data-analyst")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
