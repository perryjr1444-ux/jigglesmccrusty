"""Executive reporting agent."""
from __future__ import annotations

from typing import Dict


def compile_status_report(context: Dict[str, object]) -> Dict[str, object]:
    return {
        "case_id": context["case_id"],
        "tasks_completed": context.get("tasks_completed", 0),
        "highlights": context.get("highlights", []),
    }


def generate_device_brief(context: Dict[str, object]) -> Dict[str, object]:
    return {
        "device": context.get("device_id", "unknown"),
        "summary": context.get("summary", "Remediation successful"),
        "next_steps": context.get("next_steps", ["monitor"]),
    }
