"""Security hardening recommendations."""
from __future__ import annotations

from typing import Dict, List


def recommend_baselines(context: Dict[str, object]) -> Dict[str, List[str]]:
    controls = [
        "Enable FileVault full-disk encryption",
        "Require hardware-backed 2FA",
        "Deploy latest macOS security updates",
    ]
    return {"recommendations": controls}


def coach_user(context: Dict[str, object]) -> Dict[str, object]:
    return {
        "user": context.get("user", "unknown"),
        "next_training": context.get("next_training", "Security 101"),
        "delivery": "email",
    }
