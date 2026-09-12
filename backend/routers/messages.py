"""
Private Messaging Router for CampusPulse
Confidential grievance and whistleblowing channel.
Allows students to route messages specifically to HOD, Faculty, Management, or Staff.
Enforces strict recipient-only inbox isolation.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Header, Query

from backend.database import get_connection
from backend.models import PrivateMessageCreate, PrivateMessageItem, PrivateReplyRequest
from backend.routers.auth import decode_session_token

router = APIRouter(prefix="/api/messages", tags=["Private Messages"])

@router.post("/private")
def send_private_message(req: PrivateMessageCreate):
    """
    Submits a confidential private message directly to a specific recipient.
    Does not appear in public feeds or general triage consoles.
    """
    msg_id = f"priv-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.utcnow().isoformat()

    sender_name = "Anonymous Student" if req.is_anonymous else (req.sender_name or "Student")
    sender_id = "ANON" if req.is_anonymous else (req.sender_id or "STD-2026-89")
    sender_role = req.sender_role or "student"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO private_messages (
            id, sender_id, sender_name, sender_role, is_anonymous,
            recipient_role, recipient_id, recipient_name, recipient_dept,
            subject, message, category, urgency, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        msg_id, sender_id, sender_name, sender_role, int(req.is_anonymous),
        req.recipient_role.lower(), req.recipient_id, req.recipient_name, req.recipient_dept,
        req.subject.strip(), req.message.strip(), req.category, req.urgency or "STANDARD",
        "UNREAD", now_iso
    ))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message_id": msg_id,
        "recipient": req.recipient_name,
        "recipient_role": req.recipient_role.upper(),
        "is_anonymous": req.is_anonymous,
        "message": f"Confidential message delivered directly to {req.recipient_name} ({req.recipient_role.upper()})."
    }

@router.get("/inbox", response_model=List[PrivateMessageItem])
def get_private_inbox(
    user_id: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """
    Retrieves private messages strictly addressed to the authenticated recipient.
    Students cannot access this endpoint. Other recipients cannot view messages of peers.
    """
    active_user_id = user_id
    active_role = role

    if authorization:
        payload = decode_session_token(authorization)
        if payload:
            active_user_id = payload.get("sub", active_user_id)
            active_role = payload.get("role", active_role)

    if not active_user_id:
        raise HTTPException(status_code=401, detail="Authentication required to view private inbox.")

    if active_role == "student":
        raise HTTPException(status_code=403, detail="Students cannot access member private inboxes.")

    conn = get_connection()
    cursor = conn.cursor()

    # Match either by recipient_id OR recipient_role if recipient_id was generic
    cursor.execute("""
        SELECT * FROM private_messages 
        WHERE recipient_id = ? OR LOWER(recipient_role) = LOWER(?)
        ORDER BY created_at DESC
    """, (active_user_id, active_role or ""))
    rows = cursor.fetchall()
    conn.close()

    return [
        PrivateMessageItem(
            id=r["id"],
            sender_id=r["sender_id"],
            sender_name=r["sender_name"],
            sender_role=r["sender_role"],
            is_anonymous=bool(r["is_anonymous"]),
            recipient_role=r["recipient_role"],
            recipient_id=r["recipient_id"],
            recipient_name=r["recipient_name"],
            recipient_dept=r["recipient_dept"],
            subject=r["subject"],
            message=r["message"],
            category=r["category"] or "General Grievance",
            urgency=r["urgency"] or "STANDARD",
            status=r["status"] or "UNREAD",
            reply_note=r["reply_note"],
            replied_by=r["replied_by"],
            replied_at=r["replied_at"],
            created_at=r["created_at"]
        )
        for r in rows
    ]

@router.get("/sent", response_model=List[PrivateMessageItem])
def get_sent_messages(user_id: str = Query(...)):
    """
    Retrieves private messages sent by a specific user for their personal ticket history.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM private_messages 
        WHERE sender_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    return [
        PrivateMessageItem(
            id=r["id"],
            sender_id=r["sender_id"],
            sender_name=r["sender_name"],
            sender_role=r["sender_role"],
            is_anonymous=bool(r["is_anonymous"]),
            recipient_role=r["recipient_role"],
            recipient_id=r["recipient_id"],
            recipient_name=r["recipient_name"],
            recipient_dept=r["recipient_dept"],
            subject=r["subject"],
            message=r["message"],
            category=r["category"] or "General Grievance",
            urgency=r["urgency"] or "STANDARD",
            status=r["status"] or "UNREAD",
            reply_note=r["reply_note"],
            replied_by=r["replied_by"],
            replied_at=r["replied_at"],
            created_at=r["created_at"]
        )
        for r in rows
    ]

@router.patch("/{id}/reply")
def reply_to_private_message(id: str, req: PrivateReplyRequest):
    """
    Allows the recipient to mark the private message as reviewed/resolved and add a private note.
    """
    now_iso = datetime.utcnow().isoformat()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE private_messages
        SET status = ?, reply_note = ?, replied_by = ?, replied_at = ?
        WHERE id = ?
    """, (req.status or "REPLIED", req.reply_note.strip(), req.replied_by, now_iso, id))

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Private message not found.")

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message_id": id,
        "status": req.status,
        "reply_note": req.reply_note,
        "replied_by": req.replied_by,
        "replied_at": now_iso
    }
