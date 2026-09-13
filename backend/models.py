from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    STAFF = "STAFF"
    ADMIN = "ADMIN"
    TEAM_MANAGER = "TEAM_MANAGER"

class PriorityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class IssueStatus(str, Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

# --- Request / Response Models ---

class ComplaintCreate(BaseModel):
    text: Optional[str] = None
    raw_text: Optional[str] = None
    location_id: Optional[str] = "hostel-c-2"
    is_anonymous: bool = False
    is_private: bool = False
    recipient_role: Optional[str] = None
    recipient_id: Optional[str] = None
    recipient_name: Optional[str] = None
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    student_dept: Optional[str] = None
    attachment_url: Optional[str] = None
    image_url: Optional[str] = None

class ComplaintPreviewRequest(BaseModel):
    text: str

class ComplaintPreviewResponse(BaseModel):
    inferred_category: str
    confidence: float
    urgency: str
    extracted_location_id: Optional[str]
    potential_duplicate: bool
    matched_issue_id: Optional[str] = None
    similarity_score: Optional[float] = None
    action_note: str

class ComplaintItem(BaseModel):
    id: str
    raw_text: str
    normalized_text: str
    category: str
    category_confidence: float
    urgency: str
    location_id: str
    location_name: str
    source: str
    status: str
    is_anonymous: bool
    is_private: bool = False
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    issue_id: Optional[str] = None
    similarity_score: Optional[float] = None
    image_url: Optional[str] = None
    attachment_url: Optional[str] = None
    created_at: str

class IssueItem(BaseModel):
    id: str
    case_id: str
    title: str
    description: str
    category: str
    location_id: str
    location_name: str
    urgency: str
    priority_score: int
    priority_level: PriorityLevel
    complaint_count: int
    upvote_count: int
    assigned_team_id: str
    assigned_team_name: str
    status: IssueStatus
    jira_issue_id: Optional[str] = None
    jira_url: Optional[str] = None
    slack_alert_sent: bool = False
    ai_explanation: Optional[str] = None
    hotspot_index: int = 50
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    creator_name: Optional[str] = None
    creator_id: Optional[str] = None
    is_anonymous: bool = False
    is_private: bool = False
    has_voted: bool = False
    image_url: Optional[str] = None
    attachment_url: Optional[str] = None

class UserRole(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    HOD = "hod"
    MANAGEMENT = "management"
    STAFF = "staff"

class UserItem(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    department: Optional[str] = None
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: UserItem
    message: str

class UpvoteRequest(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = "student"

class PrivateMessageCreate(BaseModel):
    recipient_role: str  # hod, faculty, management, staff
    recipient_id: str
    recipient_name: str
    recipient_dept: Optional[str] = None
    subject: str
    message: str
    category: Optional[str] = "General Grievance"
    urgency: Optional[str] = "STANDARD"
    is_anonymous: bool = False
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_role: Optional[str] = "student"

class PrivateMessageItem(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    sender_role: str
    is_anonymous: bool
    recipient_role: str
    recipient_id: str
    recipient_name: str
    recipient_dept: Optional[str] = None
    subject: str
    message: str
    category: str
    urgency: str
    status: str
    reply_note: Optional[str] = None
    replied_by: Optional[str] = None
    replied_at: Optional[str] = None
    created_at: str

class PrivateReplyRequest(BaseModel):
    reply_note: str
    replied_by: str
    status: Optional[str] = "REPLIED"

class TimelineItem(BaseModel):
    id: Optional[int] = None
    issue_id: str
    timestamp: str
    title: str
    description: Optional[str] = None
    badge_type: Optional[str] = "info"
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    comment: Optional[str] = None

class IssueDetail(IssueItem):
    complaints: List[ComplaintItem] = []
    timeline: List[Dict[str, Any]] = []

class StatusUpdateRequest(BaseModel):
    status: IssueStatus
    note: Optional[str] = None
    comment: Optional[str] = None
    changed_by: Optional[str] = None
    changed_by_role: Optional[str] = None

class AssignTeamRequest(BaseModel):
    team_id: str
    assigned_by: Optional[str] = None

class FeedbackCreate(BaseModel):
    issue_id: Optional[str] = None
    complaint_id: Optional[str] = None
    field: str  # e.g., "category", "urgency", "priority"
    predicted_value: str
    corrected_value: str
    notes: Optional[str] = None
    corrected_by: Optional[str] = None

class UpvoteResponse(BaseModel):
    success: bool = True
    issue_id: str
    case_id: str
    upvote_count: int
    new_priority_score: int
    new_priority_level: str
    priority_level: Optional[str] = None

class DashboardSummary(BaseModel):
    total_complaints: int
    active_clusters: int
    critical_issues: int
    in_progress: int
    resolved_issues: int
    dedup_ratio: float
    dedup_percent: float
    sla_compliance_rate: float
    avg_triage_speed: str
    pipeline_active: bool

class HotspotSector(BaseModel):
    rank: int
    location_id: str
    location_name: str
    building: str
    hotspot_index: int
    severity_label: str
    category_counts: Dict[str, int]
    active_issue_count: int
    coordinates_grid: str
