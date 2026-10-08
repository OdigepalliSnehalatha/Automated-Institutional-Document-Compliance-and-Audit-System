import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.routes import auth, auditor, hod, faculty, documents, admin, ai_chat
from backend.database import get_db_cursor

SESSION_SECRET = os.getenv(
    "SESSION_SECRET",
    "alits-structural-compliance-session-key-2026"
)

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Automated Institutional Document Compliance and Audit System",
    description="Structural document comparison and institutional document management system",
    version="2.0.0"
)

# -------------------------------------------------------------
# Session Middleware (Cookie-based auth, Lax, no HTTPS requirement for dev)
# -------------------------------------------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="session",
    max_age=60 * 60 * 12,  # 12 hours
    same_site="lax",
    https_only=False
)

# -------------------------------------------------------------
# CORS Configuration (Outermost middleware)
# -------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_origin_regex=r"^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Register Routers
# -------------------------------------------------------------
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(auditor.router)
app.include_router(hod.router)
app.include_router(faculty.router)
app.include_router(documents.router)
app.include_router(ai_chat.router)

@app.get("/")
def root():
    return {
        "system": "Automated Institutional Document Compliance and Audit System",
        "version": "2.0.0",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    with get_db_cursor() as cursor:
        cursor.execute("SELECT 1 AS healthy")
        db_res = cursor.fetchone()
    return {
        "status": "healthy",
        "database": "connected" if db_res and db_res["healthy"] == 1 else "unhealthy"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)