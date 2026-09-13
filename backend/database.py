import sqlite3
import json
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "campuspulse.db")

def hash_password(password: str) -> str:
    """Computes a SHA-256 hash with salt for secure password comparison."""
    return hashlib.sha256(f"campuspulse_salt_{password}".encode("utf-8")).hexdigest()

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS locations (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        building TEXT NOT NULL,
        floor TEXT NOT NULL,
        grid_coord TEXT,
        hotspot_index INTEGER DEFAULT 50,
        latitude REAL,
        longitude REAL
    );

    CREATE TABLE IF NOT EXISTS teams (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        slack_channel TEXT NOT NULL,
        jira_project TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS issues (
        id TEXT PRIMARY KEY,
        case_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        location_id TEXT NOT NULL,
        urgency TEXT NOT NULL,
        priority_score INTEGER NOT NULL,
        priority_level TEXT NOT NULL,
        complaint_count INTEGER DEFAULT 1,
        upvote_count INTEGER DEFAULT 0,
        assigned_team_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'OPEN',
        jira_issue_id TEXT,
        jira_url TEXT,
        slack_alert_sent INTEGER DEFAULT 0,
        ai_explanation TEXT,
        hotspot_index INTEGER DEFAULT 50,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        resolved_at TEXT,
        image_url TEXT,
        FOREIGN KEY (location_id) REFERENCES locations(id),
        FOREIGN KEY (assigned_team_id) REFERENCES teams(id)
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        student_name TEXT,
        raw_text TEXT NOT NULL,
        normalized_text TEXT NOT NULL,
        embedding_json TEXT,
        category TEXT NOT NULL,
        category_confidence REAL DEFAULT 0.90,
        urgency TEXT NOT NULL,
        location_id TEXT NOT NULL,
        source TEXT DEFAULT 'web',
        status TEXT DEFAULT 'PROCESSED',
        is_anonymous INTEGER DEFAULT 1,
        issue_id TEXT,
        similarity_score REAL,
        image_url TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (location_id) REFERENCES locations(id),
        FOREIGN KEY (issue_id) REFERENCES issues(id)
    );

    CREATE TABLE IF NOT EXISTS issue_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        badge_type TEXT DEFAULT 'info',
        actor_name TEXT,
        actor_role TEXT,
        comment TEXT,
        FOREIGN KEY (issue_id) REFERENCES issues(id)
    );

    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL, -- 'student', 'faculty', 'hod', 'management', 'staff'
        department TEXT,
        email TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id TEXT,
        complaint_id TEXT,
        field TEXT NOT NULL,
        predicted_value TEXT NOT NULL,
        corrected_value TEXT NOT NULL,
        corrected_by TEXT DEFAULT 'Dean E. Vance',
        notes TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL,
        changed_by TEXT,
        old_value TEXT,
        new_value TEXT,
        timestamp TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS issue_upvotes (
        id TEXT PRIMARY KEY,
        issue_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        username TEXT,
        created_at TEXT NOT NULL,
        UNIQUE(issue_id, user_id),
        FOREIGN KEY (issue_id) REFERENCES issues(id)
    );

    CREATE TABLE IF NOT EXISTS private_messages (
        id TEXT PRIMARY KEY,
        sender_id TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        sender_role TEXT NOT NULL,
        is_anonymous INTEGER DEFAULT 0,
        recipient_role TEXT NOT NULL,
        recipient_id TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        recipient_dept TEXT,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        category TEXT,
        urgency TEXT DEFAULT 'STANDARD',
        status TEXT DEFAULT 'UNREAD',
        reply_note TEXT,
        replied_by TEXT,
        replied_at TEXT,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()

    # Safe migrations for existing tables
    cursor.execute("PRAGMA table_info(issue_timeline)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    if "actor_name" not in existing_cols:
        cursor.execute("ALTER TABLE issue_timeline ADD COLUMN actor_name TEXT")
    if "actor_role" not in existing_cols:
        cursor.execute("ALTER TABLE issue_timeline ADD COLUMN actor_role TEXT")
    if "comment" not in existing_cols:
        cursor.execute("ALTER TABLE issue_timeline ADD COLUMN comment TEXT")

    cursor.execute("PRAGMA table_info(complaints)")
    c_cols = {row["name"] for row in cursor.fetchall()}
    if "student_id" not in c_cols:
        cursor.execute("ALTER TABLE complaints ADD COLUMN student_id TEXT")
    if "is_private" not in c_cols:
        cursor.execute("ALTER TABLE complaints ADD COLUMN is_private INTEGER DEFAULT 0")
    if "recipient_id" not in c_cols:
        cursor.execute("ALTER TABLE complaints ADD COLUMN recipient_id TEXT")
    if "recipient_role" not in c_cols:
        cursor.execute("ALTER TABLE complaints ADD COLUMN recipient_role TEXT")
    if "image_url" not in c_cols:
        cursor.execute("ALTER TABLE complaints ADD COLUMN image_url TEXT")

    cursor.execute("PRAGMA table_info(issues)")
    i_cols = {row["name"] for row in cursor.fetchall()}
    if "creator_name" not in i_cols:
        cursor.execute("ALTER TABLE issues ADD COLUMN creator_name TEXT")
    if "creator_id" not in i_cols:
        cursor.execute("ALTER TABLE issues ADD COLUMN creator_id TEXT")
    if "is_anonymous" not in i_cols:
        cursor.execute("ALTER TABLE issues ADD COLUMN is_anonymous INTEGER DEFAULT 0")
    if "is_private" not in i_cols:
        cursor.execute("ALTER TABLE issues ADD COLUMN is_private INTEGER DEFAULT 0")
    if "image_url" not in i_cols:
        cursor.execute("ALTER TABLE issues ADD COLUMN image_url TEXT")

    conn.commit()

    # Pre-populate default users if empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        now_str = datetime.utcnow().isoformat()
        default_users = [
            # --- Students ---
            (
                "usr-student-1",
                "student_rohit",
                hash_password("student@123"),
                "Rohit Verma",
                "student",
                "Computer Science & Engineering",
                "rohit.verma@campus.edu",
                now_str
            ),
            (
                "usr-student-2",
                "student_priya",
                hash_password("student@123"),
                "Priya Sengupta",
                "student",
                "Electronics & Communication",
                "priya.sengupta@campus.edu",
                now_str
            ),
            (
                "usr-student-3",
                "student_arjun",
                hash_password("student@123"),
                "Arjun Das",
                "student",
                "Mechanical Engineering",
                "arjun.das@campus.edu",
                now_str
            ),
            (
                "usr-student-4",
                "student_neha",
                hash_password("student@123"),
                "Neha Roy",
                "student",
                "Civil Engineering",
                "neha.roy@campus.edu",
                now_str
            ),

            # --- Faculty ---
            (
                "usr-faculty-1",
                "prof_sharma",
                hash_password("faculty@123"),
                "Prof. Rajesh Sharma",
                "faculty",
                "Electrical Engineering",
                "rajesh.sharma@campus.edu",
                now_str
            ),
            (
                "usr-faculty-2",
                "prof_gupta",
                hash_password("faculty@123"),
                "Prof. Sunita Gupta",
                "faculty",
                "Computer Science & Engineering",
                "sunita.gupta@campus.edu",
                now_str
            ),
            (
                "usr-faculty-3",
                "prof_chatterjee",
                hash_password("faculty@123"),
                "Prof. Subhash Chatterjee",
                "faculty",
                "Civil & Infrastructure",
                "subhash.chatterjee@campus.edu",
                now_str
            ),

            # --- HODs ---
            (
                "usr-hod-1",
                "hod_cse",
                hash_password("hod@123"),
                "Dr. Ananya Mukherjee",
                "hod",
                "Computer Science & Engineering",
                "ananya.mukherjee@campus.edu",
                now_str
            ),
            (
                "usr-hod-2",
                "hod_ee",
                hash_password("hod@123"),
                "Dr. Vikramaditya Roy",
                "hod",
                "Electrical Engineering",
                "vikramaditya.roy@campus.edu",
                now_str
            ),
            (
                "usr-hod-3",
                "hod_mech",
                hash_password("hod@123"),
                "Dr. Arundhati Sen",
                "hod",
                "Mechanical Engineering",
                "arundhati.sen@campus.edu",
                now_str
            ),

            # --- Management ---
            (
                "usr-mgmt-1",
                "admin_dean",
                hash_password("mgmt@123"),
                "Dean E. Vance",
                "management",
                "Campus Administration & Student Affairs",
                "dean.vance@campus.edu",
                now_str
            ),
            (
                "usr-mgmt-2",
                "dean_academics",
                hash_password("mgmt@123"),
                "Dr. K. S. Ramanujan",
                "management",
                "Academic Affairs & Research",
                "ks.ramanujan@campus.edu",
                now_str
            ),
            (
                "usr-mgmt-3",
                "director_campus",
                hash_password("mgmt@123"),
                "Dr. Meera Iyer",
                "management",
                "Campus Director & Provost",
                "director.meera@campus.edu",
                now_str
            ),

            # --- Staff ---
            (
                "usr-staff-1",
                "staff_singh",
                hash_password("staff@123"),
                "Suresh Singh (Warden)",
                "staff",
                "Hostel Facilities & Ground Operations",
                "suresh.singh@campus.edu",
                now_str
            ),
            (
                "usr-staff-2",
                "staff_ramesh",
                hash_password("staff@123"),
                "Ramesh Kumar (Electrician)",
                "staff",
                "Campus Electrical & Power Operations",
                "ramesh.kumar@campus.edu",
                now_str
            ),
            (
                "usr-staff-3",
                "staff_anil",
                hash_password("staff@123"),
                "Anil Karmakar (Plumbing)",
                "staff",
                "Water Supply & Sanitation Maintenance",
                "anil.karmakar@campus.edu",
                now_str
            ),
            (
                "usr-staff-4",
                "staff_it_samir",
                hash_password("staff@123"),
                "Samir Dutta (IT Admin)",
                "staff",
                "IT Infrastructure & Network Helpdesk",
                "samir.dutta@campus.edu",
                now_str
            ),
        ]
        cursor.executemany(
            "INSERT INTO users (id, username, password_hash, full_name, role, department, email, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            default_users
        )
        conn.commit()

    # Pre-populate default locations and teams if empty
    cursor.execute("SELECT COUNT(*) as count FROM locations")
    if cursor.fetchone()["count"] == 0:
        default_locations = [
            ("hostel-c-2", "Hostel Block C > Floor 2 (Residential Quad)", "Hostel Block C", "Floor 2", "Grid 34-North", 94, 37.4275, -122.1697),
            ("cs-lab-3", "Computer Lab Complex > Lab 3 (Turing Wing)", "Computer Lab Complex", "Floor 1", "Grid 12-West", 68, 37.4281, -122.1702),
            ("dining-1", "Dining Hall 1 > Main Atrium & Servery", "Dining Hall 1", "Ground", "Grid 22-Central", 45, 37.4269, -122.1685),
            ("science-quad", "Science Quad > Main Academic Wing B", "Science Quad", "Wing B", "Grid 41-East", 38, 37.4290, -122.1670),
            ("lib-3-east", "Library > 3rd Floor East Reading Zone", "Main Library", "Floor 3", "Grid 15-South", 14, 37.4260, -122.1710),
        ]
        cursor.executemany(
            "INSERT INTO locations (id, name, building, floor, grid_coord, hotspot_index, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            default_locations
        )

    cursor.execute("SELECT COUNT(*) as count FROM teams")
    if cursor.fetchone()["count"] == 0:
        default_teams = [
            ("hostel-maint", "Hostel Maintenance", "Hostel / Water", "#alerts-hostel-maint", "CAMP"),
            ("it-ops", "IT Network Team", "IT / Network", "#alerts-campus-it", "IT"),
            ("electrical", "Electrical Team", "Electrical", "#alerts-electrical", "ELEC"),
            ("mess", "Mess Committee", "Food / Mess", "#alerts-mess-dining", "MESS"),
            ("facilities", "Facilities Ops", "Facilities", "#alerts-campus-ops", "FAC"),
            ("security", "Security Team", "Security", "#alerts-security", "SEC"),
        ]
        cursor.executemany(
            "INSERT INTO teams (id, name, category, slack_channel, jira_project) VALUES (?, ?, ?, ?, ?)",
            default_teams
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
