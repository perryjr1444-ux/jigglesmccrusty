"""Endpoint remediation agent."""
from __future__ import annotations

from typing import Dict


def quarantine_device(context: Dict[str, str]) -> Dict[str, object]:
    return {
        "device": context["device_id"],
        "action": "quarantine",
        "network_policy": {
            "egress": "deny",
            "ingress": "allow-support-only",
        },
    }


def schedule_patch(context: Dict[str, str]) -> Dict[str, object]:
    return {
        "device": context["device_id"],
        "patch_window": context.get("window", "immediate"),
        "packages": context.get("packages", []),
    }


def collect_forensics(context: Dict[str, str]) -> Dict[str, object]:
    return {
        "device": context["device_id"],
        "artifacts": ["memory.dmp", "filesystem.tar"],
        "ticket": context.get("ticket", "SOC-0001"),
    }
