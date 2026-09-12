import json
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter

from backend.database import get_connection
from backend.ai.engine import ai_engine

router = APIRouter(prefix="/api/demo", tags=["Demo"])

@router.post("/seed")
def seed_demo_data():
    """
    Clears & populates the database with the exact presentation deck scenario
    (247 complaints deduplicated into operational cases, Block C water crisis, Wi-Fi outage, etc.)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing dynamic tables
    cursor.execute("DELETE FROM complaints")
    cursor.execute("DELETE FROM issue_timeline")
    cursor.execute("DELETE FROM issues")
    cursor.execute("DELETE FROM feedback")
    cursor.execute("DELETE FROM audit_logs")

    now = datetime.utcnow()

    # --- Issue 1: Block C Water Crisis (Critical, 37 complaints, In Progress) ---
    issue_1_id = "issue-421"
    time_1 = (now - timedelta(hours=3, minutes=12)).isoformat()
    cursor.execute("""
        INSERT INTO issues (
            id, case_id, title, description, category, location_id, urgency,
            priority_score, priority_level, complaint_count, upvote_count,
            assigned_team_id, status, jira_issue_id, jira_url, slack_alert_sent,
            ai_explanation, hotspot_index, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_1_id,
        "ISSUE-2026-00421",
        "Water supply outage in Block C",
        "Pump #2 pressure regulator failed at 06:15 AM. Floor 2 and upper wings dry.",
        "Hostel / Water",
        "hostel-c-2",
        "CRITICAL",
        92,
        "CRITICAL",
        37,
        37,
        "hostel-maint",
        "IN_PROGRESS",
        "CAMP-421",
        "https://campuspulse.atlassian.net/browse/CAMP-421",
        1,
        "Prioritized as CRITICAL (92/100) due to CRITICAL urgency (95), 37 consolidated reports (+37 endorsements), location hotspot factor of 94, and Hostel / Water domain impact.",
        94,
        time_1,
        now.isoformat()
    ))

    # Sample complaints for Issue 1
    sample_c1 = [
        ("CMP-8921", "No water running in room 204. Tried taps for 30 minutes, completely dry.", 0.94, (now - timedelta(hours=3, minutes=8)).isoformat()),
        ("CMP-8924", "Common washroom water taps not working. Tank seems empty or pump is stopped.", 0.96, (now - timedelta(hours=3, minutes=0)).isoformat()),
        ("CMP-8931", "Floor 2 has zero water pressure. Morning classes starting soon, urgent fix needed.", 0.91, (now - timedelta(hours=2, minutes=45)).isoformat()),
        ("CMP-8945", "No tap water floor 2 Block C, shower completely dry.", 0.98, (now - timedelta(hours=2, minutes=20)).isoformat()),
    ]
    for cid, text, sim, t_c in sample_c1:
        vec = ai_engine.get_vector(text)
        cursor.execute("""
            INSERT INTO complaints (
                id, user_id, student_name, raw_text, normalized_text, embedding_json,
                category, category_confidence, urgency, location_id, source, status,
                is_anonymous, issue_id, similarity_score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid, "STD-89", "Anonymous Student", text, ai_engine.preprocess(text),
            json.dumps(vec), "Hostel / Water", 0.98, "CRITICAL", "hostel-c-2", "web",
            "PROCESSED", 1, issue_1_id, sim, t_c
        ))

    cursor.executemany("""
        INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
        VALUES (?, ?, ?, ?, ?)
    """, [
        (issue_1_id, (now - timedelta(hours=3, minutes=12)).isoformat(), "First Incident Logged", "Student report received via natural language portal.", "info"),
        (issue_1_id, (now - timedelta(hours=3, minutes=11)).isoformat(), "AI Autonomous Clustering", "Vector deduplication merged 4 early reports into cluster ISSUE-2026-00421.", "primary"),
        (issue_1_id, (now - timedelta(hours=3, minutes=10)).isoformat(), "Jira Ticket Dispatched", "Ticket CAMP-421 auto-generated and assigned to Hostel Maintenance.", "primary"),
        (issue_1_id, (now - timedelta(hours=3, minutes=9)).isoformat(), "Slack Ops Alert Sent", "High-severity alert delivered to #alerts-campus-ops and duty officer SMS.", "warning"),
        (issue_1_id, (now - timedelta(hours=1, minutes=30)).isoformat(), "Plumbing Crew On-Site", "Emergency maintenance unit arrived at Block C basement pump room.", "success")
    ])

    # --- Issue 2: CS Lab 3 Wi-Fi Gateway (High, 19 complaints, Open) ---
    issue_2_id = "issue-418"
    time_2 = (now - timedelta(hours=2, minutes=45)).isoformat()
    cursor.execute("""
        INSERT INTO issues (
            id, case_id, title, description, category, location_id, urgency,
            priority_score, priority_level, complaint_count, upvote_count,
            assigned_team_id, status, jira_issue_id, jira_url, slack_alert_sent,
            ai_explanation, hotspot_index, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_2_id,
        "ISSUE-2026-00418",
        "Wi-Fi gateway timeout in Lab 3",
        "High packet drop on VLAN 44 Access Points during midterms in Turing Wing",
        "IT / Network",
        "cs-lab-3",
        "HIGH",
        81,
        "HIGH",
        19,
        19,
        "it-ops",
        "OPEN",
        "CAMP-418",
        "https://campuspulse.atlassian.net/browse/CAMP-418",
        1,
        "Prioritized as HIGH (81/100) due to HIGH urgency (80), 19 student exam workstation impacts, and hotspot index of 68.",
        68,
        time_2,
        now.isoformat()
    ))
    cursor.execute("""
        INSERT INTO complaints (
            id, user_id, student_name, raw_text, normalized_text, embedding_json,
            category, category_confidence, urgency, location_id, source, status,
            is_anonymous, issue_id, similarity_score, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "CMP-8812", "STD-44", "Verified Student",
        "Wi-Fi dropped during midterms in CS Lab 3, terminals cannot ping gateway.",
        ai_engine.preprocess("Wi-Fi dropped during midterms in CS Lab 3"),
        json.dumps(ai_engine.get_vector("Wi-Fi dropped during midterms in CS Lab 3")),
        "IT / Network", 0.95, "HIGH", "cs-lab-3", "web", "PROCESSED", 0, issue_2_id, 1.0, time_2
    ))

    # --- Issue 3: Emergency Lighting (Assigned, 12 complaints) ---
    issue_3_id = "issue-415"
    time_3 = (now - timedelta(hours=4, minutes=10)).isoformat()
    cursor.execute("""
        INSERT INTO issues (
            id, case_id, title, description, category, location_id, urgency,
            priority_score, priority_level, complaint_count, upvote_count,
            assigned_team_id, status, jira_issue_id, jira_url, slack_alert_sent,
            ai_explanation, hotspot_index, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_3_id,
        "ISSUE-2026-00415",
        "Corridor emergency lighting failure",
        "Exit stairwells pitch dark during evening classes in Academic Wing B",
        "Electrical",
        "science-quad",
        "HIGH",
        78,
        "HIGH",
        12,
        5,
        "electrical",
        "ASSIGNED",
        "CAMP-415",
        "https://campuspulse.atlassian.net/browse/CAMP-415",
        1,
        "Prioritized as HIGH (78/100) due to electrical safety risk and multi-floor exit visibility hazard.",
        38,
        time_3,
        now.isoformat()
    ))

    # --- Issue 4: Food Serving Temperature (Open, 8 complaints) ---
    issue_4_id = "issue-409"
    time_4 = (now - timedelta(hours=5, minutes=30)).isoformat()
    cursor.execute("""
        INSERT INTO issues (
            id, case_id, title, description, category, location_id, urgency,
            priority_score, priority_level, complaint_count, upvote_count,
            assigned_team_id, status, jira_issue_id, jira_url, slack_alert_sent,
            ai_explanation, hotspot_index, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_4_id,
        "ISSUE-2026-00409",
        "Food serving temperature in Dining Hall 1",
        "Bain-marie heaters cycling off during peak lunch hours",
        "Food / Mess",
        "dining-1",
        "MEDIUM",
        64,
        "MEDIUM",
        8,
        3,
        "mess",
        "OPEN",
        "CAMP-409",
        "https://campuspulse.atlassian.net/browse/CAMP-409",
        0,
        "Prioritized as MEDIUM (64/100) based on dining hygiene temperature standards and 8 student notices.",
        45,
        time_4,
        now.isoformat()
    ))

    # --- Issue 5: Ergonomic Library Chairs (Resolved, 3 complaints) ---
    issue_5_id = "issue-398"
    time_5 = (now - timedelta(days=1)).isoformat()
    time_5_res = (now - timedelta(hours=6)).isoformat()
    cursor.execute("""
        INSERT INTO issues (
            id, case_id, title, description, category, location_id, urgency,
            priority_score, priority_level, complaint_count, upvote_count,
            assigned_team_id, status, jira_issue_id, jira_url, slack_alert_sent,
            ai_explanation, hotspot_index, created_at, updated_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_5_id,
        "ISSUE-2026-00398",
        "Request ergonomic study chairs in East Library",
        "30 new seating units deployed & inventoried by Facilities Operations",
        "Academics / Facilities",
        "lib-3-east",
        "LOW",
        42,
        "LOW",
        3,
        1,
        "facilities",
        "RESOLVED",
        "CAMP-398",
        "https://campuspulse.atlassian.net/browse/CAMP-398",
        0,
        "Resolved within SLA. New ergonomic study seating deployed.",
        14,
        time_5,
        time_5_res,
        time_5_res
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Demo scenario seeded successfully with 5 core cases and sample complaints matching presentation deck."
    }

@router.post("/run-scenario")
def run_four_student_scenario():
    """
    Simulates the exact 4-student demo scenario from Section 39:
    Student 1: "No water in Block C since 8 AM."
    Student 2: "Water supply has stopped in C block."
    Student 3: "Hostel C has no water."
    Student 4: "No water coming in Block C bathrooms."
    Demonstrating real-time deduplication into 1 unified master issue.
    """
    complaints = [
        ("No water in Block C since 8 AM.", "STD-01", "Aarav S."),
        ("Water supply has stopped in C block.", "STD-02", "Priya K."),
        ("Hostel C has no water.", "STD-03", "Rohan M."),
        ("No water coming in Block C bathrooms.", "STD-04", "Neha T.")
    ]

    from backend.routers.complaints import submit_complaint
    from backend.models import ComplaintCreate

    results = []
    for text, sid, sname in complaints:
        res = submit_complaint(ComplaintCreate(
            text=text,
            location_id="hostel-c-2",
            is_anonymous=False,
            student_id=sid,
            student_name=sname
        ))
        results.append({
            "student": sname,
            "complaint_text": text,
            "result": res
        })

    return {
        "scenario": "4 Students -> 1 Unified Issue",
        "results": results
    }
