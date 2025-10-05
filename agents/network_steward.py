"""Network containment agent."""
from __future__ import annotations

from typing import Dict

from connectors.carrier import CarrierClient
from connectors.router import RouterClient


def reset_router(context: Dict[str, str]) -> Dict[str, object]:
    client = RouterClient(host=context.get("router_host", "192.168.1.1"))
    return client.factory_reset()


def rotate_wifi(context: Dict[str, str]) -> Dict[str, object]:
    client = RouterClient(host=context.get("router_host", "192.168.1.1"))
    return client.rotate_wifi_credentials(context.get("ssid", "CorpNet"))


def lock_carrier_port_out(context: Dict[str, str]) -> Dict[str, object]:
    client = CarrierClient(carrier=context.get("carrier", "CarrierCo"))
    return client.enable_port_out_lock(context.get("phone_number", "unknown"))
