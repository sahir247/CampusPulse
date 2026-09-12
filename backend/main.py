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

@app.get("/api/teams", tags=["Metadata"])
def get_all_teams():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
