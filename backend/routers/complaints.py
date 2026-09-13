import json
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from backend.database import get_connection
from backend.models import (
    ComplaintCreate, ComplaintPreviewRequest, ComplaintPreviewResponse,
    ComplaintItem
)
from backend.ai.engine import ai_engine
from backend.integrations.jira import jira_service
from backend.integrations.slack import slack_service

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

@router.post("/preview", response_model=ComplaintPreviewResponse)
def preview_complaint_nlp(req: ComplaintPreviewRequest):
    """
    Real-time typing feedback for students: infers category, urgency, location, and duplicate cluster.
    """
    text = req.text.strip()
    if not text:
        return ComplaintPreviewResponse(
            inferred_category="General Inquiry",
            confidence=0.50,
            urgency="LOW",
            extracted_location_id=None,
            potential_duplicate=False,
            action_note="Type your complaint in natural language..."
        )

    category, confidence = ai_engine.classify_category(text)
    urgency = ai_engine.detect_urgency(text, category)
    extracted_loc = ai_engine.extract_location(text)
    input_vec = ai_engine.get_vector(text)

    # Check vector similarity against active database issues
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, case_id, title, description, category, location_id, complaint_count 
        FROM issues 
        WHERE status IN ('OPEN', 'ASSIGNED', 'IN_PROGRESS')
    """)
    active_issues = cursor.fetchall()
    conn.close()

    best_match_id = None
    best_case_id = None
    best_sim = 0.0

    for issue in active_issues:
        target_text = f"{issue['title']} {issue['description'] or ''} {issue['category']}"
        sim = ai_engine.compute_semantic_match(
            query_text=text,
            query_cat=category,
            query_loc=extracted_loc,
            candidate_text=target_text,
            candidate_cat=issue["category"],
            candidate_loc=issue["location_id"]
        )

        if sim > best_sim:
            best_sim = sim
            best_match_id = issue["id"]
            best_case_id = issue["case_id"]

    best_sim = round(best_sim, 2)
    is_duplicate = best_sim >= getattr(ai_engine, "calibrated_threshold", 0.65)

    if is_duplicate:
        action_note = f"Detected {int(best_sim * 100)}% vector overlap with cluster #{best_case_id}. Merges on submit."
    else:
        action_note = f"New independent issue cluster will be provisioned."

    return ComplaintPreviewResponse(
        inferred_category=category,
        confidence=confidence,
        urgency=urgency,
        extracted_location_id=extracted_loc,
        potential_duplicate=is_duplicate,
        matched_issue_id=best_case_id if is_duplicate else None,
        similarity_score=best_sim,
        action_note=action_note
    )

@router.post("")
def submit_complaint(payload: ComplaintCreate):
    """
    Intake raw complaint -> NLP Preprocessing -> Vector Embedding ->
    Deduplication against active Issues -> Auto-Merge or New Issue ->
    Calculate Multi-Factor Priority -> Dispatch Jira/Slack.
    """
    input_text = (payload.text or payload.raw_text or "").strip()
    if len(input_text) < 5:
        raise HTTPException(status_code=400, detail="Complaint text is too short.")

    now_iso = datetime.utcnow().isoformat()
    complaint_id = f"CMP-{uuid.uuid4().hex[:6].upper()}"
    raw_text = input_text
    normalized_text = ai_engine.preprocess(raw_text)
    complaint_vec = ai_engine.get_vector(raw_text)

    # Classify & assess
    category, confidence = ai_engine.classify_category(raw_text)
    urgency = ai_engine.detect_urgency(raw_text, category)
    
    # Location selection: user input takes priority, otherwise AI extracted
    location_id = payload.location_id
    if not location_id:
        location_id = ai_engine.extract_location(raw_text) or "hostel-c-2"

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch location details for hotspot weight
    cursor.execute("SELECT name, hotspot_index FROM locations WHERE id = ?", (location_id,))
    loc_row = cursor.fetchone()
    loc_name = loc_row["name"] if loc_row else "Campus Facility"
    loc_hotspot = loc_row["hotspot_index"] if loc_row else 50

    # Dynamically resolve creator identity from payload or users table
    creator_display_name = "Anonymous Student"
    creator_user_id = None
    if not payload.is_anonymous:
        if payload.student_id:
            cursor.execute("SELECT id, full_name, username FROM users WHERE id = ? OR username = ?", (payload.student_id, payload.student_id))
            usr = cursor.fetchone()
            if usr:
                creator_display_name = usr["full_name"]
                creator_user_id = usr["id"]
            else:
                creator_display_name = payload.student_name or "Verified Student"
                creator_user_id = payload.student_id
        else:
            creator_display_name = payload.student_name or "Verified Student"
            creator_user_id = None

    # Search active issues for semantic duplicate matching
    cursor.execute("""
        SELECT id, case_id, title, description, category, location_id, urgency,
               complaint_count, upvote_count, assigned_team_id, hotspot_index,
               jira_issue_id, status
        FROM issues
        WHERE status IN ('OPEN', 'ASSIGNED', 'IN_PROGRESS')
    """)
    active_issues = cursor.fetchall()

    best_match = None
    highest_similarity = 0.0

    for issue in active_issues:
        target_text = f"{issue['title']} {issue['description'] or ''} {issue['category']}"
        sim = ai_engine.compute_semantic_match(
            query_text=raw_text,
            query_cat=category,
            query_loc=location_id,
            candidate_text=target_text,
            candidate_cat=issue["category"],
            candidate_loc=issue["location_id"]
        )

        if sim > highest_similarity:
            highest_similarity = sim
            best_match = issue

    highest_similarity = round(highest_similarity, 2)
    merged = False
    assigned_issue_id = None
    case_id_display = None

    # Extract photo / attachment URL if provided
    img_url = payload.attachment_url or payload.image_url

    # DEDUPLICATION THRESHOLD: Empirical calibrated threshold (default 0.65)
    threshold = getattr(ai_engine, "calibrated_threshold", 0.65)
    if best_match and highest_similarity >= threshold:
        merged = True
        assigned_issue_id = best_match["id"]
        case_id_display = best_match["case_id"]
        new_complaint_count = best_match["complaint_count"] + 1

        # Re-evaluate priority score with new report count
        new_score, new_level, new_explanation = ai_engine.calculate_priority(
            urgency=best_match["urgency"],
            complaint_count=new_complaint_count,
            upvote_count=best_match["upvote_count"],
            category=best_match["category"],
            hotspot_index=best_match["hotspot_index"]
        )

        cursor.execute("""
            UPDATE issues
            SET complaint_count = ?,
                priority_score = ?,
                priority_level = ?,
                ai_explanation = ?,
                updated_at = ?
            WHERE id = ?
        """, (new_complaint_count, new_score, new_level, new_explanation, now_iso, assigned_issue_id))

        if img_url:
            cursor.execute("""
                UPDATE issues
                SET image_url = ?
                WHERE id = ? AND (image_url IS NULL OR image_url = '')
            """, (img_url, assigned_issue_id))

        # Add timeline entry
        cursor.execute("""
            INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            assigned_issue_id,
            now_iso,
            f"Deduplication Match ({int(highest_similarity * 100)}%)",
            f"Complaint #{complaint_id} merged into cluster. Total reports now: {new_complaint_count}.",
            "primary"
        ))

    else:
        # Create NEW consolidated Issue entity
        assigned_issue_id = str(uuid.uuid4())
        cursor.execute("SELECT COUNT(*) as cnt FROM issues")
        total_issues = cursor.fetchone()["cnt"] + 1
        case_id_display = f"ISSUE-2026-00{total_issues:03d}"

        assigned_team_id = ai_engine.route_team(category)
        cursor.execute("SELECT name, slack_channel, jira_project FROM teams WHERE id = ?", (assigned_team_id,))
        team_row = cursor.fetchone()
        team_name = team_row["name"] if team_row else "Facilities Ops"
        slack_channel = team_row["slack_channel"] if team_row else "#alerts-campus-ops"
        jira_project = team_row["jira_project"] if team_row else "CAMP"

        score, level, explanation = ai_engine.calculate_priority(
            urgency=urgency,
            complaint_count=1,
            upvote_count=0,
            category=category,
            hotspot_index=loc_hotspot
        )

        # Generate Jira Ticket
        jira_ticket = jira_service.create_ticket(
            case_id=case_id_display,
            title=raw_text[:60],
            category=category,
            priority_level=level,
            location_name=loc_name,
            complaint_count=1,
            project_key=jira_project
        )

        # Dispatch Slack Alert
        slack_sent = False
        if level in ["CRITICAL", "HIGH"]:
            slack_service.dispatch_alert(
                case_id=case_id_display,
                title=raw_text[:60],
                category=category,
                priority_level=level,
                priority_score=score,
                location_name=loc_name,
                complaint_count=1,
                assigned_team=team_name,
                slack_channel=slack_channel,
                jira_id=jira_ticket["jira_issue_id"]
            )
            slack_sent = True

        cursor.execute("""
            INSERT INTO issues (
                id, case_id, title, description, category, location_id, urgency,
                priority_score, priority_level, complaint_count, upvote_count,
                assigned_team_id, status, jira_issue_id, jira_url, slack_alert_sent,
                ai_explanation, hotspot_index, created_at, updated_at,
                creator_name, creator_id, is_anonymous, is_private, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assigned_issue_id,
            case_id_display,
            raw_text[:60],
            raw_text,
            category,
            location_id,
            urgency,
            score,
            level,
            1,
            0,
            assigned_team_id,
            "OPEN",
            jira_ticket["jira_issue_id"],
            jira_ticket["jira_url"],
            1 if slack_sent else 0,
            explanation,
            loc_hotspot,
            now_iso,
            now_iso,
            creator_display_name,
            creator_user_id,
            1 if payload.is_anonymous else 0,
            1 if payload.is_private else 0,
            img_url
        ))

        cursor.execute("""
            INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
            VALUES (?, ?, ?, ?, ?)
        """, (
            assigned_issue_id,
            now_iso,
            "Cluster Created & Routed",
            f"Autonomous triage routed issue to {team_name}. Jira: {jira_ticket['jira_issue_id']}",
            "success"
        ))

    # Save Complaint record with reference to consolidated Issue
    cursor.execute("""
        INSERT INTO complaints (
            id, user_id, student_name, student_id, raw_text, normalized_text, embedding_json,
            category, category_confidence, urgency, location_id, source, status,
            is_anonymous, is_private, recipient_id, recipient_role, issue_id, similarity_score, image_url, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        creator_user_id if not payload.is_anonymous else None,
        creator_display_name if not payload.is_anonymous else "Anonymous Student",
        creator_user_id if not payload.is_anonymous else None,
        raw_text,
        normalized_text,
        json.dumps(complaint_vec),
        category,
        confidence,
        urgency,
        location_id,
        "web",
        "PROCESSED",
        1 if payload.is_anonymous else 0,
        1 if payload.is_private else 0,
        payload.recipient_id,
        payload.recipient_role,
        assigned_issue_id,
        highest_similarity if merged else 1.0,
        img_url,
        now_iso
    ))

    # Audit log
    cursor.execute("""
        INSERT INTO audit_logs (entity_type, entity_id, action, changed_by, old_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "COMPLAINT",
        complaint_id,
        "DEDUPLICATED_MERGE" if merged else "NEW_ISSUE_CREATED",
        "AI_ENGINE",
        None,
        f"Linked to {case_id_display} (Similarity: {highest_similarity})",
        now_iso
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "complaint_id": complaint_id,
        "merged_into_existing": merged,
        "issue_id": assigned_issue_id,
        "case_id": case_id_display,
        "category": category,
        "urgency": urgency,
        "similarity_score": highest_similarity if merged else 1.0,
        "image_url": img_url,
        "message": f"Complaint successfully processed. Consolidated under {case_id_display}."
    }

@router.get("", response_model=List[ComplaintItem])
def list_complaints(issue_id: Optional[str] = None, category: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.*, l.name as location_name 
        FROM complaints c
        LEFT JOIN locations l ON c.location_id = l.id
        WHERE 1=1
    """
    params = []

    if issue_id:
        query += " AND c.issue_id = ?"
        params.append(issue_id)
    if category:
        query += " AND c.category = ?"
        params.append(category)

    query += " ORDER BY c.created_at DESC LIMIT 100"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        ComplaintItem(
            id=r["id"],
            raw_text=r["raw_text"],
            normalized_text=r["normalized_text"],
            category=r["category"],
            category_confidence=r["category_confidence"] or 0.9,
            urgency=r["urgency"],
            location_id=r["location_id"],
            location_name=r["location_name"] or "Campus Facility",
            source=r["source"] or "web",
            status=r["status"] or "PROCESSED",
            is_anonymous=bool(r["is_anonymous"]),
            issue_id=r["issue_id"],
            similarity_score=r["similarity_score"],
            image_url=r["image_url"] if "image_url" in r.keys() else None,
            attachment_url=r["image_url"] if "image_url" in r.keys() else None,
            created_at=r["created_at"]
        )
        for r in rows
    ]
