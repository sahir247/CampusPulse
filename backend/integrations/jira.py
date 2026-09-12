import datetime
from typing import Dict, Any, Optional

class JiraIntegrationService:
    def __init__(self):
        self.base_url = "https://campuspulse.atlassian.net/browse"
        self.counter = 430

    def create_ticket(
        self,
        case_id: str,
        title: str,
        category: str,
        priority_level: str,
        location_name: str,
        complaint_count: int,
        project_key: str = "CAMP"
    ) -> Dict[str, Any]:
        """
        Simulate/Execute creation of a Jira ticket for a consolidated campus issue.
        """
        self.counter += 1
        jira_id = f"{project_key}-{self.counter}"
        jira_url = f"{self.base_url}/{jira_id}"

        priority_mapping = {
            "CRITICAL": "Highest",
            "HIGH": "High",
            "MEDIUM": "Medium",
            "LOW": "Low"
        }

        ticket_payload = {
            "jira_issue_id": jira_id,
            "jira_url": jira_url,
            "project": project_key,
            "summary": f"[{case_id}] {title}",
            "priority": priority_mapping.get(priority_level, "Medium"),
            "category": category,
            "location": location_name,
            "reports_count": complaint_count,
            "labels": ["campuspulse", "autonomous-dispatch", category.lower().replace(" ", "-")],
            "status": "OPEN",
            "created_at": datetime.datetime.utcnow().isoformat()
        }
        return ticket_payload

    def sync_status_from_jira(self, jira_status: str) -> str:
        """
        Map incoming Jira webhook transitions to CampusPulse operational status.
        """
        s = jira_status.upper()
        if "PROGRESS" in s:
            return "IN_PROGRESS"
        elif "RESOLVE" in s or "DONE" in s:
            return "RESOLVED"
        elif "CLOSE" in s:
            return "CLOSED"
        elif "ASSIGN" in s:
            return "ASSIGNED"
        return "OPEN"

jira_service = JiraIntegrationService()
