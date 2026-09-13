import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from backend.database import get_connection
from backend.models import (
    IssueItem, IssueDetail, ComplaintItem, StatusUpdateRequest,
    AssignTeamRequest, FeedbackCreate, UpvoteResponse, UpvoteRequest
)
from backend.ai.engine import ai_engine

router = APIRouter(prefix="/api/issues", tags=["Issues"])

@router.get("", response_model=List[IssueItem])
def list_issues(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    team: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = None,
    active_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    conn = get_connection()
    cursor = conn.cursor()

    user_voted_set = set()
    if user_id:
        cursor.execute("SELECT issue_id FROM issue_upvotes WHERE user_id = ? OR username = ?", (user_id, user_id))
        user_voted_set = {r["issue_id"] for r in cursor.fetchall()}

    query = """
        SELECT i.*, l.name as location_name, t.name as assigned_team_name
        FROM issues i
        LEFT JOIN locations l ON i.location_id = l.id
        LEFT JOIN teams t ON i.assigned_team_id = t.id
        WHERE (i.is_private = 0 OR i.is_private IS NULL)
    """
    params = []

    if category and category.lower() != "all":
        query += " AND (LOWER(i.category) LIKE ? OR LOWER(i.category) LIKE ?)"
        params.extend([f"%{category.lower()}%", f"%{category.lower()}%"])

    if priority and priority.lower() != "all":
        query += " AND LOWER(i.priority_level) = ?"
        params.append(priority.lower())

    if team and team.lower() != "all":
        query += " AND (i.assigned_team_id = ? OR LOWER(t.name) LIKE ?)"
        params.extend([team, f"%{team.lower()}%"])

    if status and status.lower() not in ("all", ""):
        if status.lower() == "active":
            query += " AND i.status IN ('OPEN', 'ASSIGNED', 'IN_PROGRESS')"
        elif status.lower() == "resolved":
            query += " AND i.status IN ('RESOLVED', 'CLOSED')"
        else:
            query += " AND LOWER(i.status) = ?"
            params.append(status.lower())
    elif active_only:
        query += " AND i.status IN ('OPEN', 'ASSIGNED', 'IN_PROGRESS')"

    if search:
        s = f"%{search.lower()}%"
        query += " AND (LOWER(i.case_id) LIKE ? OR LOWER(i.title) LIKE ? OR LOWER(i.description) LIKE ? OR LOWER(i.jira_issue_id) LIKE ? OR LOWER(l.name) LIKE ?)"
        params.extend([s, s, s, s, s])

    query += " ORDER BY i.priority_score DESC, i.updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        IssueItem(
            id=r["id"],
            case_id=r["case_id"],
            title=r["title"],
            description=r["description"] or "",
            category=r["category"],
            location_id=r["location_id"],
            location_name=r["location_name"] or "Campus Location",
            urgency=r["urgency"],
            priority_score=r["priority_score"],
            priority_level=r["priority_level"],
            complaint_count=r["complaint_count"],
            upvote_count=r["upvote_count"] or 0,
            assigned_team_id=r["assigned_team_id"],
            assigned_team_name=r["assigned_team_name"] or "Campus Ops",
            status=r["status"],
            jira_issue_id=r["jira_issue_id"],
            jira_url=r["jira_url"],
            slack_alert_sent=bool(r["slack_alert_sent"]),
            ai_explanation=r["ai_explanation"],
            hotspot_index=r["hotspot_index"] or 50,
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            resolved_at=r["resolved_at"],
            creator_name="Anonymous Student" if ("is_anonymous" in r.keys() and r["is_anonymous"]) else (r["creator_name"] if "creator_name" in r.keys() and r["creator_name"] else "Verified Student"),
            creator_id=None if ("is_anonymous" in r.keys() and r["is_anonymous"]) else (r["creator_id"] if "creator_id" in r.keys() else None),
            is_anonymous=bool(r["is_anonymous"]) if "is_anonymous" in r.keys() else False,
            is_private=bool(r["is_private"]) if "is_private" in r.keys() else False,
            has_voted=bool(r["id"] in user_voted_set),
            image_url=r["image_url"] if "image_url" in r.keys() else None,
            attachment_url=r["image_url"] if "image_url" in r.keys() else None
        )
        for r in rows
    ]

@router.get("/archive/resolved", response_model=List[IssueItem])
def get_resolved_archive(search: Optional[str] = None, limit: int = 50):
    """Returns all past resolved and closed tickets for the historical archive."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT i.*, l.name as location_name, t.name as assigned_team_name
        FROM issues i
        LEFT JOIN locations l ON i.location_id = l.id
        LEFT JOIN teams t ON i.assigned_team_id = t.id
        WHERE i.status IN ('RESOLVED', 'CLOSED')
    """
    params = []
    if search:
        s = f"%{search.lower()}%"
        query += " AND (LOWER(i.case_id) LIKE ? OR LOWER(i.title) LIKE ? OR LOWER(i.description) LIKE ? OR LOWER(l.name) LIKE ?)"
        params.extend([s, s, s, s])
    query += " ORDER BY i.resolved_at DESC, i.updated_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        IssueItem(
            id=r["id"],
            case_id=r["case_id"],
            title=r["title"],
            description=r["description"] or "",
            category=r["category"],
            location_id=r["location_id"],
            location_name=r["location_name"] or "Campus Location",
            urgency=r["urgency"],
            priority_score=r["priority_score"],
            priority_level=r["priority_level"],
            complaint_count=r["complaint_count"],
            upvote_count=r["upvote_count"] or 0,
            assigned_team_id=r["assigned_team_id"],
            assigned_team_name=r["assigned_team_name"] or "Campus Ops",
            status=r["status"],
            jira_issue_id=r["jira_issue_id"],
            jira_url=r["jira_url"],
            slack_alert_sent=bool(r["slack_alert_sent"]),
            ai_explanation=r["ai_explanation"],
            hotspot_index=r["hotspot_index"] or 50,
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            resolved_at=r["resolved_at"],
            creator_name="Anonymous Student" if ("is_anonymous" in r.keys() and r["is_anonymous"]) else (r["creator_name"] if "creator_name" in r.keys() and r["creator_name"] else "Student"),
            creator_id=None if ("is_anonymous" in r.keys() and r["is_anonymous"]) else (r["creator_id"] if "creator_id" in r.keys() else None),
            is_anonymous=bool(r["is_anonymous"]) if "is_anonymous" in r.keys() else False,
            is_private=bool(r["is_private"]) if "is_private" in r.keys() else False,
            has_voted=False,
            image_url=r["image_url"] if "image_url" in r.keys() else None,
            attachment_url=r["image_url"] if "image_url" in r.keys() else None
        )
        for r in rows
    ]

@router.get("/user/my-tickets")
def get_student_ticket_history(student_id: Optional[str] = None, user_id: Optional[str] = None, username: Optional[str] = None):
    """Retrieves all tickets and complaints associated with this student dynamically."""
    query_id = student_id or user_id or username
    if not query_id:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    valid_ids = [query_id]
    cursor.execute("SELECT id, username, full_name FROM users WHERE id = ? OR username = ?", (query_id, query_id))
    usr = cursor.fetchone()
    if usr:
        valid_ids.extend([usr["id"], usr["username"]])
    valid_ids = list(set(valid_ids))
    placeholders = ",".join(["?"] * len(valid_ids))

    cursor.execute(f"""
        SELECT c.id as complaint_id, c.raw_text, c.category, c.urgency, c.created_at as reported_at,
               c.is_anonymous, c.is_private, c.status as complaint_status,
               c.image_url as complaint_image_url, c.image_url as image_url,
               i.id as issue_id, i.case_id, i.title as issue_title, i.status as issue_status,
               i.priority_level, i.complaint_count, i.upvote_count,
               i.image_url as issue_image_url,
               l.name as location_name, t.name as assigned_team_name, i.resolved_at
        FROM complaints c
        LEFT JOIN issues i ON c.issue_id = i.id
        LEFT JOIN locations l ON c.location_id = l.id
        LEFT JOIN teams t ON i.assigned_team_id = t.id
        WHERE c.user_id IN ({placeholders}) 
           OR c.student_id IN ({placeholders})
           OR i.creator_id IN ({placeholders})
        ORDER BY c.created_at DESC
    """, valid_ids * 3)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/{id}", response_model=IssueDetail)
def get_issue_detail(id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.*, l.name as location_name, t.name as assigned_team_name
        FROM issues i
        LEFT JOIN locations l ON i.location_id = l.id
        LEFT JOIN teams t ON i.assigned_team_id = t.id
        WHERE i.id = ? OR i.case_id = ?
    """, (id, id))
    r = cursor.fetchone()

    if not r:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    issue_id = r["id"]

    # Fetch child complaints
    cursor.execute("""
        SELECT c.*, l.name as location_name
        FROM complaints c
        LEFT JOIN locations l ON c.location_id = l.id
        WHERE c.issue_id = ?
        ORDER BY c.created_at DESC
    """, (issue_id,))
    complaint_rows = cursor.fetchall()

    # Fetch timeline
    cursor.execute("""
        SELECT * FROM issue_timeline
        WHERE issue_id = ?
        ORDER BY timestamp ASC
    """, (issue_id,))
    timeline_rows = cursor.fetchall()

    conn.close()

    complaints = [
        ComplaintItem(
            id=c["id"],
            raw_text=c["raw_text"],
            normalized_text=c["normalized_text"],
            category=c["category"],
            category_confidence=c["category_confidence"] or 0.9,
            urgency=c["urgency"],
            location_id=c["location_id"],
            location_name=c["location_name"] or "Campus Location",
            source=c["source"] or "web",
            status=c["status"] or "PROCESSED",
            is_anonymous=bool(c["is_anonymous"]),
            issue_id=c["issue_id"],
            similarity_score=c["similarity_score"],
            image_url=c["image_url"] if "image_url" in c.keys() else None,
            attachment_url=c["image_url"] if "image_url" in c.keys() else None,
            created_at=c["created_at"]
        )
        for c in complaint_rows
    ]

    timeline = [
        {
            "id": t["id"],
            "timestamp": t["timestamp"],
            "title": t["title"],
            "description": t["description"],
            "badge_type": t["badge_type"],
            "actor_name": t["actor_name"] if "actor_name" in t.keys() else None,
            "actor_role": t["actor_role"] if "actor_role" in t.keys() else None,
            "comment": t["comment"] if "comment" in t.keys() else None
        }
        for t in timeline_rows
    ]

    return IssueDetail(
        id=r["id"],
        case_id=r["case_id"],
        title=r["title"],
        description=r["description"] or "",
        category=r["category"],
        location_id=r["location_id"],
        location_name=r["location_name"] or "Campus Location",
        urgency=r["urgency"],
        priority_score=r["priority_score"],
        priority_level=r["priority_level"],
        complaint_count=r["complaint_count"],
        upvote_count=r["upvote_count"],
        assigned_team_id=r["assigned_team_id"],
        assigned_team_name=r["assigned_team_name"] or "Campus Ops",
        status=r["status"],
        jira_issue_id=r["jira_issue_id"],
        jira_url=r["jira_url"],
        slack_alert_sent=bool(r["slack_alert_sent"]),
        ai_explanation=r["ai_explanation"],
        hotspot_index=r["hotspot_index"] or 50,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        resolved_at=r["resolved_at"],
        creator_name="Anonymous Student" if ("is_anonymous" in r.keys() and r["is_anonymous"]) else (r["creator_name"] if "creator_name" in r.keys() and r["creator_name"] else "Verified Student"),
        creator_id=None if ("is_anonymous" in r.keys() and r["is_anonymous"]) else (r["creator_id"] if "creator_id" in r.keys() else None),
        is_anonymous=bool(r["is_anonymous"]) if "is_anonymous" in r.keys() else False,
        is_private=bool(r["is_private"]) if "is_private" in r.keys() else False,
        has_voted=False,
        image_url=r["image_url"] if "image_url" in r.keys() else None,
        attachment_url=r["image_url"] if "image_url" in r.keys() else None,
        complaints=complaints,
        timeline=timeline
    )

@router.get("/{id}/timeline")
def get_issue_timeline(id: str):
    """Retrieve full chronological action log for a ticket."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, case_id FROM issues WHERE id = ? OR case_id = ?", (id, id))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    cursor.execute("""
        SELECT id, issue_id, timestamp, title, description, badge_type, actor_name, actor_role, comment
        FROM issue_timeline
        WHERE issue_id = ?
        ORDER BY id DESC
    """, (issue["id"],))
    timeline_rows = cursor.fetchall()
    conn.close()

    return [dict(t) for t in timeline_rows]

@router.patch("/{id}/status")
def update_issue_status(id: str, req: StatusUpdateRequest):
    actor_role = (req.changed_by_role or "staff").lower().strip()
    actor_name = (req.changed_by or "Campus Staff").strip()

    # RBAC Guard: Students cannot change ticket status
    if actor_role == "student":
        raise HTTPException(
            status_code=403,
            detail="Permission Denied: Students are not permitted to change ticket status. Only faculty, HOD, management, and staff can mark ticket actions."
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ? OR case_id = ?", (id, id))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    now_iso = datetime.utcnow().isoformat()
    old_status = issue["status"]
    new_status = req.status.value
    resolved_at = now_iso if new_status == "RESOLVED" else issue["resolved_at"]

    cursor.execute("""
        UPDATE issues
        SET status = ?, resolved_at = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, resolved_at, now_iso, issue["id"]))

    # Clean formatted action log with role and optional comment
    status_display = new_status.replace("_", " ").title()
    action_title = f"{status_display} marked by {actor_name}"
    comment_text = req.comment.strip() if req.comment and req.comment.strip() else (req.note.strip() if req.note and req.note.strip() else None)
    
    desc = f"{status_display} marked by {actor_name} (Role: {actor_role.upper()})"
    if comment_text:
        desc += f' — Comment: "{comment_text}"'

    badge_type = "success" if new_status in ("RESOLVED", "CLOSED") else "warning" if new_status == "IN_PROGRESS" else "info"

    cursor.execute("""
        INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type, actor_name, actor_role, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (issue["id"], now_iso, action_title, desc, badge_type, actor_name, actor_role.upper(), comment_text))

    # Audit log
    cursor.execute("""
        INSERT INTO audit_logs (entity_type, entity_id, action, changed_by, old_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("ISSUE", issue["case_id"], f"STATUS_CHANGE_{new_status}", f"{actor_name} ({actor_role})", old_status, new_status, now_iso))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "case_id": issue["case_id"],
        "old_status": old_status,
        "new_status": new_status,
        "marked_by": actor_name,
        "role": actor_role.upper(),
        "comment": comment_text,
        "action_log_entry": desc
    }

@router.patch("/{id}/assign")
def reassign_team(id: str, req: AssignTeamRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ? OR case_id = ?", (id, id))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    cursor.execute("SELECT name FROM teams WHERE id = ?", (req.team_id,))
    team_row = cursor.fetchone()
    if not team_row:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid team ID")

    now_iso = datetime.utcnow().isoformat()
    new_team_name = team_row["name"]

    cursor.execute("""
        UPDATE issues
        SET assigned_team_id = ?, updated_at = ?
        WHERE id = ?
    """, (req.team_id, now_iso, issue["id"]))

    cursor.execute("""
        INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
        VALUES (?, ?, ?, ?, ?)
    """, (issue["id"], now_iso, "Reassigned", f"Case reassigned to {new_team_name} by {req.assigned_by}", "warning"))

    conn.commit()
    conn.close()

    return {"success": True, "case_id": issue["case_id"], "assigned_team": new_team_name}

@router.post("/{id}/upvote", response_model=UpvoteResponse)
def upvote_issue(id: str, req: Optional[UpvoteRequest] = None):
    """
    Increment 'I have this issue too' counter for student endorsements:
    - Enforces: Only students can vote
    - Enforces: One vote per student per ticket
    - Records: Student endorsement in action log & audit log
    - Dynamic: Elevates priority and urgency as votes accumulate
    """
    if not req or not req.user_id:
        raise HTTPException(
            status_code=400,
            detail="Authentication required: user_id must be provided to endorse an issue."
        )

    conn = get_connection()
    cursor = conn.cursor()

    # Dynamically verify user from database
    cursor.execute("SELECT id, username, full_name, role FROM users WHERE id = ? OR username = ?", (req.user_id, req.username or req.user_id))
    user_row = cursor.fetchone()
    if user_row:
        user_id = user_row["id"]
        username = user_row["username"]
        full_name = user_row["full_name"]
        user_role = user_row["role"].lower()
    else:
        user_id = req.user_id.strip()
        username = (req.username or req.user_id).strip()
        full_name = username
        user_role = (req.user_role or "student").lower().strip()

    if user_role != "student":
        conn.close()
        raise HTTPException(
            status_code=403,
            detail="Permission Denied: Only students can endorse issues with 'I have this issue too'. Other roles can view endorsement counts."
        )

    cursor.execute("SELECT * FROM issues WHERE id = ? OR case_id = ?", (id, id))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    issue_id = issue["id"]

    # Check for existing vote by this student (check both user_id and username)
    cursor.execute("SELECT id FROM issue_upvotes WHERE issue_id = ? AND (user_id = ? OR username = ?)", (issue_id, user_id, username))
    existing_vote = cursor.fetchone()
    if existing_vote:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="You have already endorsed this issue. Each student can vote once per ticket."
        )

    now_iso = datetime.utcnow().isoformat()
    vote_id = f"vote-{uuid.uuid4().hex[:8]}"

    # Insert into issue_upvotes
    cursor.execute("""
        INSERT INTO issue_upvotes (id, issue_id, user_id, username, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (vote_id, issue_id, user_id, username, now_iso))

    new_upvotes = (issue["upvote_count"] or 0) + 1

    # Dynamic Urgency Elevation based on accumulated student endorsements
    current_urgency = issue["urgency"]
    if new_upvotes >= 15 or (new_upvotes + (issue["complaint_count"] or 0)) >= 20:
        new_urgency = "CRITICAL"
    elif new_upvotes >= 6:
        new_urgency = "HIGH" if current_urgency != "CRITICAL" else "CRITICAL"
    else:
        new_urgency = current_urgency

    # Recalculate priority with new votes and elevated urgency
    new_score, new_level, explanation = ai_engine.calculate_priority(
        urgency=new_urgency,
        complaint_count=issue["complaint_count"],
        upvote_count=new_upvotes,
        category=issue["category"],
        hotspot_index=issue["hotspot_index"]
    )

    if new_upvotes >= 12 and new_level != "CRITICAL":
        new_level = "CRITICAL"

    cursor.execute("""
        UPDATE issues
        SET upvote_count = ?,
            urgency = ?,
            priority_score = ?,
            priority_level = ?,
            ai_explanation = ?,
            updated_at = ?
        WHERE id = ?
    """, (new_upvotes, new_urgency, new_score, new_level, explanation, now_iso, issue_id))

    # Record endorsement event in action log / timeline
    cursor.execute("""
        INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type, actor_name, actor_role, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        issue_id,
        now_iso,
        "Student Endorsement (+1)",
        f"{full_name} (@{username}) confirmed: 'I have this issue too'. Total student endorsements: {new_upvotes}.",
        "primary",
        full_name,
        "student",
        f"Endorsed issue. Elevated priority to {new_level} (Score: {new_score})."
    ))

    # Record in audit logs
    cursor.execute("""
        INSERT INTO audit_logs (entity_type, entity_id, action, changed_by, old_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "ISSUE",
        issue_id,
        "STUDENT_ENDORSEMENT",
        f"{full_name} ({username})",
        str(issue["upvote_count"] or 0),
        str(new_upvotes),
        now_iso
    ))

    conn.commit()
    conn.close()

    return UpvoteResponse(
        success=True,
        issue_id=issue["id"],
        case_id=issue["case_id"],
        upvote_count=new_upvotes,
        new_priority_score=new_score,
        new_priority_level=new_level,
        priority_level=new_level
    )

@router.post("/{id}/feedback")
def submit_admin_feedback(id: str, fb: FeedbackCreate):
    """
    Active learning feedback: Admin corrects AI classification or priority.
    Saved to evaluation dataset for scheduled fine-tuning/retraining.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM issues WHERE id = ? OR case_id = ?", (id, id))
    issue = cursor.fetchone()
    if not issue:
        conn.close()
        raise HTTPException(status_code=404, detail="Issue not found")

    now_iso = datetime.utcnow().isoformat()

    # Save to feedback table
    cursor.execute("""
        INSERT INTO feedback (issue_id, complaint_id, field, predicted_value, corrected_value, corrected_by, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (issue["id"], fb.complaint_id, fb.field, fb.predicted_value, fb.corrected_value, fb.corrected_by, fb.notes, now_iso))

    # Apply correction immediately to issue
    if fb.field.lower() == "category":
        new_team_id = ai_engine.route_team(fb.corrected_value)
        cursor.execute("""
            UPDATE issues
            SET category = ?, assigned_team_id = ?, updated_at = ?
            WHERE id = ?
        """, (fb.corrected_value, new_team_id, now_iso, issue["id"]))

    cursor.execute("""
        INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
        VALUES (?, ?, ?, ?, ?)
    """, (issue["id"], now_iso, "AI Corrected", f"Category corrected from {fb.predicted_value} to {fb.corrected_value} by {fb.corrected_by}.", "primary"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Active learning feedback captured for {issue['case_id']}. Updated in live database."
    }
