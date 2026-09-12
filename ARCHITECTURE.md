# CampusPulse (Campus+) — Architecture & Technical Design

## 1. Executive Summary & Core Philosophy

**CampusPulse** is an enterprise-grade, intelligent campus incident reporting, semantic deduplication, and resolution tracking system. In large collegiate environments, facility breakdowns (e.g., water leaks, AC failures, electrical hazards, broken equipment) typically suffer from:
1. **Complaint Avalanche & Duplicate Noise**: Dozens of students report the same broken water cooler or lab PC using slightly different wording across multiple languages (English, Hindi, Bengali).
2. **Context Loss & Lack of Traceability**: Maintenance staff mark tickets as "In Progress" or "Resolved" without accountability, audit logs, or administrative notes.
3. **Role Sprawl & Information Clutter**: Students are overwhelmed by administrative controls, while faculty/management lack clean incident triage tools.
4. **Time Discrepancies**: Global UTC timestamps confuse campus teams operating on standard local time (IST).

CampusPulse eliminates these bottlenecks through a **Zero-Noise, High-Accuracy Architecture**:
- **Trilingual Multilingual NLP Engine** powered by `paraphrase-multilingual-mpnet-base-v2`.
- **Vector-Based Semantic Deduplication ($\ge 0.72$ Cosine Similarity)** clustering redundant complaints into unified master tickets.
- **Strict Role-Based Access Control (RBAC)** across Student, Faculty, HOD, Management, and Staff.
- **Single-Vote Student Endorsement Engine ("I have this issue too")** boosting real-time urgency without duplicate tickets.
- **Immutable Action Log Audit Trail** capturing actor name, role, timestamp in **Indian Standard Time (IST)**, and mandatory/optional resolution comments.
- **Confidential Leadership Routing** for sensitive grievances submitted directly to HODs and Deans.

---

## 2. High-Level System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["Frontend Layer (Vanilla Web & Tailwind / Modern Glassmorphism)"]
        UI_Student["Student Portal\n- Incident Reporting\n- Live Issue Feed\n- 'I have this issue too' (+1 Vote)\n- Ticket History & Confidential Sent"]
        UI_Faculty["Faculty / Staff Console\n- Dynamic Incident Triage\n- Action Log Inspector\n- Status Transition Modal\n- Merged Complaint Drawer"]
        UI_HOD["Leadership / HOD Hub\n- Confidential Private Inbox\n- Department Incident Matrix\n- Executive Action Overrides"]
    end

    subgraph APILayer["FastAPI Application Server (Port 8000)"]
        Router_Auth["/api/auth\nJWT & Cookie Session RBAC"]
        Router_Complaints["/api/complaints\nReporting & Previews"]
        Router_Issues["/api/issues\nLifecycle, Upvotes & History"]
        Router_Messages["/api/messages\nConfidential Routing & Replies"]
        Router_Recipients["/api/recipients\nLeadership Directory"]
        Router_Analytics["/api/analytics\nKPIs & Campus Hotspots"]
    end

    subgraph AIEngine["AI & NLP Pipeline"]
        Embedder["Sentence-Transformers\n(paraphrase-multilingual-mpnet-base-v2)\n768-dimensional Dense Vectors"]
        Classifier["Ridge Classifier\n9 Campus Incident Categories\nTrilingual (EN, HI, BN)"]
        DedupEngine["Cosine Similarity Cluster Engine\nThreshold >= 0.72 Matching"]
        PriorityEngine["Multi-Factor Priority Formula\nUrgency + Impact + Location Tier"]
    end

    subgraph DataLayer["Storage & Audit Layer (SQLite WAL Mode)"]
        DB_Users[("users\nCredentials, Roles, Dept")]
        DB_Issues[("issues\nMaster Incidents & Priorities")]
        DB_Complaints[("complaints\nRaw Reports & Vector Embeddings")]
        DB_Upvotes[("issue_upvotes\nStrict 1-Vote per Student")]
        DB_Timeline[("issue_timeline\nAudit History & Comments")]
        DB_Messages[("private_messages\nConfidential Leadership Inquiries")]
    end

    subgraph IntegrationLayer["External Connectors"]
        JiraSync["Jira Cloud REST API\nAutomated Service Desk Tickets"]
        SlackSync["Slack Webhook\nEmergency Alert Dispatch (IST)"]
    end

    %% Connections
    UI_Student --> Router_Complaints
    UI_Student --> Router_Issues
    UI_Student --> Router_Messages
    UI_Faculty --> Router_Issues
    UI_Faculty --> Router_Analytics
    UI_HOD --> Router_Messages
    UI_HOD --> Router_Issues

    Router_Complaints --> AIEngine
    Router_Complaints --> DataLayer
    Router_Issues --> DataLayer
    Router_Messages --> DataLayer
    Router_Auth --> DB_Users

    AIEngine --> PriorityEngine
    PriorityEngine --> DB_Issues

    Router_Issues --> JiraSync
    Router_Issues --> SlackSync
```

---

## 3. Multilingual NLP & Deduplication Pipeline

CampusPulse guarantees **zero duplicate work orders** through a 3-stage natural language pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student (Reporter)
    participant UI as Client UI (Live Preview)
    participant API as FastAPI /api/complaints
    participant NLP as MPNet Embedder (768-d)
    participant Ridge as Ridge Classifier
    participant DB as SQLite Database
    participant Ext as Jira / Slack

    Student->>UI: Types: "পানি পড়ার জন্য ল্যাবে শর্টসার্কিট হতে পারে" (Bengali)
    UI->>API: POST /api/complaints/preview
    API->>NLP: Generate 768-d dense embedding
    NLP->>Ridge: Predict Category & Confidence
    Ridge-->>API: Category: "Electrical & Safety" (0.94 conf)
    API->>DB: Query open issues in location
    API->>API: Compute Cosine Similarities against active vectors
    alt Match found (Similarity >= 0.72)
        API-->>UI: Return matched issue ID & "Linked to existing issue" warning
    else No Match (< 0.72)
        API-->>UI: Return New Incident candidate
    end

    Student->>UI: Clicks "Submit Report"
    UI->>API: POST /api/complaints
    alt Is Duplicate / Match >= 0.72
        API->>DB: Append complaint to existing Issue
        API->>DB: Increment complaint_count & recalculate priority
        API->>DB: Insert into issue_timeline (Audit: Deduplicated Report)
    else New Issue
        API->>DB: Create new master Issue
        API->>DB: Insert into issue_timeline (Audit: Ticket Created)
        API->>Ext: Dispatch Jira ticket & Slack alert (with IST timestamp)
    end
    API-->>UI: Confirmation with Case ID & SLA
```

### 3.1 Model Architecture & Specifications
- **Embedding Model**: `paraphrase-multilingual-mpnet-base-v2` (768 embedding dimensions, 128 max sequence length, normalized Euclidean unit vectors).
- **Linguistic Coverage**:
  - **English**: Formal and colloquial campus complaints.
  - **Hindi (Devanagari & Romanized Hinglish)**: e.g., *"कंप्यूटर लैब में एसी काम नहीं कर रहा"* and *"water cooler leak ho raha hai"*.
  - **Bengali (Bengali script & Romanized)**: e.g., *"ল্যাব ৩ এ ফ্যান ঘুরছে না"* and *"pani porche bathroom e"*.
- **Classification Head**: L2-regularized linear Ridge classifier trained across 9 campus operational categories:
  1. `Infrastructure & Civil`
  2. `Electrical & Safety`
  3. `Water & Sanitation`
  4. `IT & Network Equipment`
  5. `HVAC & Ventilation`
  6. `Hostel & Residential Facilities`
  7. `Library & Study Spaces`
  8. `Canteen & Food Services`
  9. `Campus Security & Surveillance`

### 3.2 Mathematical Deduplication Formulation
Given an incoming complaint $c_{new}$ with 768-d normalized embedding vector $\mathbf{v}_{new}$ and a set of currently active open issues $\{I_1, I_2, \dots, I_m\}$ within the same or neighboring campus zone:

$$\text{Cosine Similarity}(c_{new}, I_k) = \frac{\mathbf{v}_{new} \cdot \mathbf{v}_{I_k}}{\|\mathbf{v}_{new}\| \|\mathbf{v}_{I_k}\|} = \mathbf{v}_{new} \cdot \mathbf{v}_{I_k} \quad (\text{since } \|\mathbf{v}\| = 1)$$

$$\text{Deduplication Decision} = \begin{cases} \text{Merge into } I^* = \arg\max_k \text{Sim}(c_{new}, I_k) & \text{if } \max_k \text{Sim} \ge 0.72 \\ \text{Create New Incident Ticket} & \text{otherwise} \end{cases}$$

---

## 4. Multi-Factor Priority Escalation Engine

Every incident ticket dynamically evaluates a priority score $S \in [0, 100]$ upon every new student report or single-vote endorsement:

$$S = \min\left(100, \left(W_{\text{cat}} \times C\right) + \left(W_{\text{loc}} \times L\right) + \left(W_{\text{urg}} \times U\right) + \left(W_{\text{vol}} \times \ln(1 + N_{\text{reports}} + 0.5 \times N_{\text{votes}})\right)\right)$$

Where:
- **Category Severity ($C \in [10, 40]$)**: Electrical & Safety ($40$), Water & Sanitation ($30$), IT Infrastructure ($25$), General Civil ($15$).
- **Location Sensitivity ($L \in [10, 30]$)**: Server Rooms, Substations & Chem Labs ($30$), Classrooms & Library ($20$), Corridors & Open Grounds ($10$).
- **Student Endorsement Headcount ($N_{\text{reports}}, N_{\text{votes}}$)**: Sub-linear logarithmic amplification ensuring issues with 25+ endorsements automatically breach the **Critical Tier ($S \ge 75$)**.

```mermaid
graph LR
    Submissions[Complaints & Endorsements] --> Volume[Logarithmic Impact Curve]
    Hazard[Safety / Emergency Keyword Scan] --> Severity[Category Weight]
    Zone[High-Risk / Academic Labs] --> Location[Location Tier]

    Volume --> Aggregator[Priority Aggregator]
    Severity --> Aggregator
    Location --> Aggregator

    Aggregator --> Triage{Score Tier}
    Triage -->|Score >= 75| P1[CRITICAL - 2 Hr SLA]
    Triage -->|Score 50-74| P2[HIGH - 6 Hr SLA]
    Triage -->|Score 25-49| P3[MEDIUM - 24 Hr SLA]
    Triage -->|Score < 25| P4[LOW - 48 Hr SLA]
```

---

## 5. Role-Based Access Control (RBAC) & View Isolation

CampusPulse strictly enforces least-privilege access at both the API and client presentation tiers:

| Role | Incident Reporting | Endorsement Voting | Incident Console Triage | Show Action Log | Add Action Comments | Confidential Leadership Inbox |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Student** | Yes (Public / Anon / Private) | **Yes** (Strict 1-vote/ticket) | No (Hidden) | Yes (View-only) | No | No (Only view own sent replies) |
| **Faculty** | View / Track | No (View count only) | **Yes** (Update status) | Yes | **Yes** (With status update) | No |
| **HOD** | View / Track | No (View count only) | **Yes** (Department view) | Yes | **Yes** (With status update) | **Yes** (Direct student inquiries) |
| **Management** | View / Track | No (View count only) | **Yes** (Campus-wide view) | Yes | **Yes** (Executive override) | **Yes** (Campus-wide appeals) |
| **Staff** | View / Track | No (View count only) | **Yes** (Assigned tasks) | Yes | **Yes** (Work log notes) | No |

### View-Filtering Rules
1. **Student View**: Displays only the **Report an Issue** form, the **Campus Live Issues** feed, and **My Ticket History**. Administrative tabs are never rendered in the DOM for students.
2. **Staff / Faculty View**: Displays the unclipped **Incident Console** and **Resolved Archive**. The student reporting form and leadership inbox are omitted.
3. **Leadership View (HOD & Management)**: Displays the **Confidential Inbox**, **Incident Console**, and **Resolved Archive**.

---

## 6. Database Schema & Entity Relationship Diagram (ERD)

The persistent store is built on **SQLite 3** running with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`), foreign keys enabled, and indexing on lookups.

```mermaid
erDiagram
    USERS ||--o{ COMPLAINTS : "submits"
    USERS ||--o{ ISSUE_UPVOTES : "endorses"
    USERS ||--o{ ISSUE_TIMELINE : "logs action"
    USERS ||--o{ PRIVATE_MESSAGES : "sends/receives"
    ISSUES ||--o{ COMPLAINTS : "aggregates"
    ISSUES ||--o{ ISSUE_UPVOTES : "receives"
    ISSUES ||--o{ ISSUE_TIMELINE : "tracks audit"

    USERS {
        string id PK "usr-student-1, usr-hod-1"
        string username "Unique login ID"
        string password_hash "Bcrypt or Argon2 hash"
        string full_name "Display name"
        string role "student | faculty | hod | management | staff"
        string department "Computer Science, Facilities, etc."
        string email "Campus email"
        datetime created_at "ISO-8601 UTC"
    }

    ISSUES {
        string id PK "issue-2026-00418"
        string case_id "CAMP-418"
        string title "Canonical issue title"
        string description "Consolidated description"
        string category "Civil, Electrical, IT, etc."
        string location_name "Lab 302, CS Block"
        string status "OPEN | ASSIGNED | IN_PROGRESS | RESOLVED | CLOSED"
        string priority_level "LOW | MEDIUM | HIGH | CRITICAL"
        integer priority_score "0 to 100"
        integer complaint_count "Number of merged reports"
        integer upvote_count "Number of student endorsements"
        string assigned_team_name "Electrical Maintenance"
        string jira_issue_id "JIRA-4819"
        string creator_id "Foreign key to users.id"
        string creator_name "Name of first student reporter"
        boolean is_anonymous "Redacted if anonymous"
        datetime created_at "ISO-8601 UTC"
        datetime resolved_at "ISO-8601 UTC"
    }

    COMPLAINTS {
        string id PK "comp-8f921"
        string issue_id FK "References issues.id"
        string user_id FK "References users.id"
        string raw_text "Original multilingual text"
        string language_detected "en | hi | bn"
        string location_name "Location reported"
        boolean is_anonymous "Flag indicating privacy"
        blob vector_embedding "768-float binary serialization"
        datetime created_at "ISO-8601 UTC"
    }

    ISSUE_UPVOTES {
        integer id PK "Auto-incrementing"
        string issue_id FK "References issues.id"
        string user_id FK "References users.id"
        datetime created_at "ISO-8601 UTC"
    }

    ISSUE_TIMELINE {
        string id PK "evt-91283"
        string issue_id FK "References issues.id"
        string event_type "STATUS_CHANGE | DEDUPLICATION | ENDORSEMENT | ESCALATION"
        string title "Action headline"
        string description "Detailed event description"
        string actor_name "Prof. Rajesh Sharma"
        string actor_role "faculty | hod | staff | student"
        string comment "Optional administrative reason"
        datetime timestamp "ISO-8601 UTC"
    }

    PRIVATE_MESSAGES {
        string id PK "priv-239022c8"
        string sender_id FK "References users.id"
        string sender_name "Student Name or Anonymous"
        string sender_role "student"
        boolean is_anonymous "True if sender redacted"
        string recipient_role "hod | management"
        string recipient_id FK "References users.id"
        string recipient_name "Dr. Ananya Mukherjee"
        string recipient_dept "Computer Science"
        string subject "Confidential Subject"
        string message "Full body text"
        string status "PENDING | REPLIED"
        string reply_note "Confidential administrative reply"
        datetime created_at "ISO-8601 UTC"
        datetime replied_at "ISO-8601 UTC"
    }
```

---

## 7. Timezone Standard: Indian Standard Time (IST)

To prevent operational ambiguity between student submissions, maintenance rounds, and administrative sign-offs:
1. **Persistence Protocol**: Stored internally as standard UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SS.mmmmmmZ`) for universal database consistency.
2. **Client-Side Rendering**: Normalized via `formatISTTime()`:
   ```javascript
   function formatISTTime(dateStr, includeSeconds = false) {
     let normalizedStr = String(dateStr).trim();
     if (!normalizedStr.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(normalizedStr)) {
       normalizedStr += 'Z';
     }
     const d = new Date(normalizedStr);
     return `${d.toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', ... })} IST`;
   }
   ```
   *Displays as:* `12 Sep, 03:07 PM IST` across all student cards, ticket tables, audit timelines, and leadership inboxes.
3. **Outbound Webhooks**: Slack alerts and external dispatches format timestamps directly in Indian Standard Time (`UTC+05:30`):
   ```python
   ist_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
   timestamp_str = ist_now.strftime('%I:%M:%S %p IST')
   ```

---

## 8. External Integration Architecture

```mermaid
graph TD
    IssueCreated[Master Ticket Created / Escalated] --> Dispatcher{Event Broker}
    
    Dispatcher -->|Async Webhook| JiraWorker[Jira Cloud REST Connector]
    JiraWorker --> JiraEndpoint[POST /rest/api/3/issue\nCustom Campus Scheme]
    JiraEndpoint --> JiraResponse[Return JIRA-KEY\nStore in issues.jira_issue_id]
    
    Dispatcher -->|Async Webhook| SlackWorker[Slack Webhook Connector]
    SlackWorker --> SlackPayload["Format Block Kit Payload\nLocation, Priority, Merged Count, IST Time"]
    SlackPayload --> SlackAPI[POST to #campus-ops channel]
```

- **Jira Cloud Connector**: Synchronizes high-priority campus issues into Jira Service Management projects, mapping categories to campus maintenance components.
- **Slack Operations Connector**: Formats rich Slack Block Kit cards with interactive urgency badges and direct links to the CampusPulse Incident Console.
