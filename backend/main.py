import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db, get_connection
from backend.routers import complaints, issues, dashboard, webhooks, demo, auth, messages

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist and seed demo data if empty
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM issues")
    count = cursor.fetchone()["cnt"]
    conn.close()

    if count == 0:
        print("Auto-seeding initial CampusPulse demonstration dataset...")
        demo.seed_demo_data()

    yield
    # Shutdown

app = FastAPI(
    title="CampusPulse Civic Intel OS",
    description="Autonomous Issue Resolution and Intelligence Monolith",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(messages.router)
app.include_router(complaints.router)
app.include_router(issues.router)
app.include_router(dashboard.router)
app.include_router(webhooks.router)
app.include_router(demo.router)

# Locations and Teams lookup endpoints
@app.get("/api/recipients", tags=["Metadata"])
def get_recipients():
    """Returns directory of possible private message recipients (HODs, Faculty, Management, Staff)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, department 
        FROM users 
        WHERE role != 'student'
        ORDER BY role ASC, full_name ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# Locations and Teams lookup endpoints
@app.get("/api/locations", tags=["Metadata"])
def get_all_locations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM locations ORDER BY hotspot_index DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# Locations and Teams lookup endpoints
@app.get("/api/teams", tags=["Metadata"])
def get_all_teams():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# File Upload Endpoint & Uploads Static Directory
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

from fastapi import UploadFile, File, Form, HTTPException
import uuid

@app.post("/api/upload", tags=["Uploads"])
async def upload_attachment(file: UploadFile = File(...)):
    """Uploads an incident photo / attachment and returns its accessible static URL."""
    try:
        # Read content and validate size (10MB limit)
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File exceeds maximum size of 10MB.")
        
        # Determine safe extension
        ext = os.path.splitext(file.filename or "")[1].lower()
        if not ext or ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"]:
            ext = ".jpg"
            
        unique_name = f"evidence_{uuid.uuid4().hex[:12]}{ext}"
        target_path = os.path.join(uploads_dir, unique_name)
        
        with open(target_path, "wb") as f:
            f.write(contents)
            
        return {
            "success": True,
            "filename": unique_name,
            "url": f"/uploads/{unique_name}",
            "size": len(contents)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
