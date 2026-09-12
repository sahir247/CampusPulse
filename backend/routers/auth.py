"""
Authentication & RBAC Router for CampusPulse
Supports login, session retrieval, and quick demo user switching across roles:
- student
- faculty
- hod
- management
- staff
"""

import base64
import json
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List

from backend.database import get_connection, hash_password
from backend.models import LoginRequest, LoginResponse, UserItem

router = APIRouter()

def create_session_token(user: dict) -> str:
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"]
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    return f"campus_{encoded}"

def decode_session_token(token: str) -> Optional[dict]:
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        if token.startswith("campus_"):
            raw = token[7:]
            payload_bytes = base64.urlsafe_b64decode(raw.encode())
            return json.loads(payload_bytes.decode())
    except Exception:
        return None
    return None

@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Authenticate user with username and password."""
    username = req.username.strip().lower()
    password = req.password.strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    expected_hash = user["password_hash"]
    given_hash = hash_password(password)

    if given_hash != expected_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    user_dict = dict(user)
    token = create_session_token(user_dict)

    user_item = UserItem(
        id=user_dict["id"],
        username=user_dict["username"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        department=user_dict.get("department"),
        email=user_dict.get("email")
    )

    return LoginResponse(
        success=True,
        token=token,
        user=user_item,
        message=f"Welcome back, {user_dict['full_name']} ({user_dict['role'].upper()})."
    )

@router.get("/me", response_model=UserItem)
def get_current_user(authorization: Optional[str] = Header(None)):
    """Retrieve profile of current logged-in user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing.")

    payload = decode_session_token(authorization)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, department, email FROM users WHERE id = ?", (payload["sub"],))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    return UserItem(**dict(user))

@router.get("/demo-users", response_model=List[UserItem])
def get_demo_users():
    """Returns list of dummy demo users across all 5 roles for 1-click quick switching."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, department, email FROM users ORDER BY role DESC")
    users = cursor.fetchall()
    conn.close()
    return [UserItem(**dict(u)) for u in users]
