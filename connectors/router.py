"""Router reset helpers."""
from __future__ import annotations

from typing import Dict


class RouterClient:
    def __init__(self, host: str) -> None:
        self.host = host

    def factory_reset(self) -> Dict[str, str]:
        return {
            "host": self.host,
            "action": "factory_reset",
            "status": "scheduled",
        }

    def rotate_wifi_credentials(self, ssid: str) -> Dict[str, str]:
        return {
            "host": self.host,
            "ssid": ssid,
            "action": "rotate_wifi_credentials",
            "status": "success",
        }
