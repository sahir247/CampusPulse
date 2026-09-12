import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body

from backend.database import get_connection
from backend.integrations.jira import jira_service

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])

@router.post("/jira")
def handle_jira_webhook(payload: Dict[str, Any] = Body(...)):
    """
    Receives Jira status transition webhooks and mirrors the state into CampusPulse issue store.
    """
    jira_issue = payload.get("issue", {})
    jira_key = jira_issue.get("key")
    if not jira_key:
        raise HTTPException(status_code=400, detail="Missing Jira issue key in payload.")

    status_obj = jira_issue.get("fields", {}).get("status", {})
    jira_status_name = status_obj.get("name", "In Progress")

    campus_status = jira_service.sync_status_from_jira(jira_status_name)
    now_iso = datetime.datetime.utcnow().isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, case_id, status FROM issues WHERE jira_issue_id = ?", (jira_key,))
    issue = cursor.fetchone()

    if not issue:
        conn.close()
        return {"status": "ignored", "message": f"No CampusPulse issue linked to {jira_key}"}

    old_status = issue["status"]
    resolved_at = now_iso if campus_status == "RESOLVED" else None

    cursor.execute("""
        UPDATE issues
        SET status = ?, resolved_at = COALESCE(?, resolved_at), updated_at = ?
        WHERE id = ?
    """, (campus_status, resolved_at, now_iso, issue["id"]))

    cursor.execute("""
        INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
        VALUES (?, ?, ?, ?, ?)
    """, (
        issue["id"],
        now_iso,
        f"Jira Synchronized: {jira_status_name}",
        f"Automated webhook mirrored Jira ticket {jira_key} transition into CampusPulse ({campus_status}).",
        "primary"
    ))

    cursor.execute("""
        INSERT INTO audit_logs (entity_type, entity_id, action, changed_by, old_value, new_value, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, ("ISSUE", issue["case_id"], "JIRA_WEBHOOK_SYNC", f"Jira:{jira_key}", old_status, campus_status, now_iso))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "case_id": issue["case_id"],
        "jira_key": jira_key,
        "old_status": old_status,
        "new_status": campus_status
    }

@router.post("/slack")
def handle_slack_interaction(payload: Dict[str, Any] = Body(...)):
    """
    Receives interactive actions from Slack alert buttons (e.g. 'Acknowledge Dispatch', 'Escalate').
    """
    action_type = payload.get("action", "acknowledge")
    case_id = payload.get("case_id", "ISSUE-2026-00421")
    user = payload.get("user", "HostelDutyOfficer")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM issues WHERE case_id = ?", (case_id,))
    row = cursor.fetchone()

    if row:
        now_iso = datetime.datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO issue_timeline (issue_id, timestamp, title, description, badge_type)
            VALUES (?, ?, ?, ?, ?)
        """, (row["id"], now_iso, "Slack Acknowledgment", f"Alert acknowledged by {user} in #alerts-campus-ops.", "success"))
        conn.commit()

    conn.close()
    return {"success": True, "message": f"Slack action '{action_type}' recorded for {case_id}"}
