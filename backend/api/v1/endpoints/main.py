import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.v1.endpoints.documents import router as documents_router

app = FastAPI(
    title="JinOps Underwriting API Engine",
    version="1.0.0",
    description="High-Precision Credit Underwriting API for MSME Lending"
)

# CORS Configuration for local index.html frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Documents & Underwriting API Routes
app.include_router(documents_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "engine": "JinOps High-Precision Credit Engine",
        "message": "Welcome to JinOps API Engine"
    }