import os
import secrets

# --- Security ---
# Use a secure random key if not set in environment (Note: restarts will invalidate sessions)
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

# --- External API ---
CODEMAO_PID = os.getenv("CODEMAO_PID", "65edCTyg")

# --- Database ---
DATABASE_URL = "database.db"

# --- Rate Limiting ---
# (Configs for slowapi could go here if needed)

# --- Anti-Scraping ---
BLOCKED_USER_AGENTS = ["python-requests", "curl", "wget", "scrapy", "httpie"]
ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://192.227.152.240:8080"]
