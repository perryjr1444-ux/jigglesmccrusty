"""Evidence collection agent."""
from __future__ import annotations

from typing import Dict

from utils.redactor import Redactor


def collect_mailbox_evidence(context: Dict[str, str]) -> Dict[str, object]:
    redactor = Redactor()
    sensitive = {
        "suspicious_forward": context.get("forward_to", "unknown@example.com"),
        "rules": ",".join(context.get("rules", [])),
    }
    return {
        "redacted": redactor.redact(sensitive),
        "raw": sensitive,
    }


def summarize_alert(context: Dict[str, str]) -> Dict[str, object]:
    return {
        "alert_id": context.get("alert_id", "ALERT-1"),
        "summary": context.get("summary", "Mailbox forwarding detected"),
    }
