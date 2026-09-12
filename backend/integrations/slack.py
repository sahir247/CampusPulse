import datetime
from typing import Dict, Any, List

class SlackNotificationService:
    def __init__(self):
        self.sent_alerts: List[Dict[str, Any]] = []

    def dispatch_alert(
        self,
        case_id: str,
        title: str,
        category: str,
        priority_level: str,
        priority_score: int,
        location_name: str,
        complaint_count: int,
        assigned_team: str,
        slack_channel: str,
        jira_id: str
    ) -> Dict[str, Any]:
        """
        Dispatches a rich Slack Alert block payload to operational response channels.
        """
        emoji = "🚨" if priority_level == "CRITICAL" else "⚠️"
        alert_title = f"{emoji} {priority_level} CAMPUS ISSUE: {case_id}"

        payload = {
            "channel": slack_channel,
            "text": alert_title,
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": alert_title}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Issue Title:*\n{title}"},
                        {"type": "mrkdwn", "text": f"*Category:*\n{category}"},
                        {"type": "mrkdwn", "text": f"*Location:*\n{location_name}"},
                        {"type": "mrkdwn", "text": f"*Priority:*\n{priority_level} ({priority_score}/100)"},
                        {"type": "mrkdwn", "text": f"*Report Count:*\n{complaint_count} student reports"},
                        {"type": "mrkdwn", "text": f"*Assigned Team:*\n{assigned_team}"},
                        {"type": "mrkdwn", "text": f"*Jira Ticket:*\n`{jira_id}`"}
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Dispatched automatically by CampusPulse AI Engine • {datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime('%I:%M:%S %p IST')}"}
                    ]
                }
            ],
            "timestamp": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).isoformat(),
            "delivered": True
        }

        self.sent_alerts.append(payload)
        return payload

slack_service = SlackNotificationService()
