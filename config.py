import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "mpact-dev-secret-change-me")
    _db_url = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'mpact.db')}",
    )
    # Railway (and Heroku) may return postgres:// — SQLAlchemy requires postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB resume cap
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "uploads")

    # Recruiter credentials (session-based auth)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@mpact.rw")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "mpact2026")

    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Email (SMTP)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "")

    # Branding
    BRAND_NAME = "Mpact"
    BRAND_TAGLINE = "Smart recruiting for African teams."
    TEAM_NAME = "Team M&P — Mugisha Kayishema & Principie Cyubahiro"
