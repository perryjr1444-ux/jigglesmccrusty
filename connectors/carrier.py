"""Carrier lock helpers."""
from __future__ import annotations

from typing import Dict


class CarrierClient:
    def __init__(self, carrier: str) -> None:
        self.carrier = carrier

    def enable_port_out_lock(self, phone_number: str) -> Dict[str, str]:
        return {
            "carrier": self.carrier,
            "phone_number": phone_number,
            "action": "enable_port_out_lock",
            "status": "success",
        }

    def disable_port_out_lock(self, phone_number: str) -> Dict[str, str]:
        return {
            "carrier": self.carrier,
            "phone_number": phone_number,
            "action": "disable_port_out_lock",
            "status": "success",
        }
