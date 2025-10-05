"""Playbook loader and DAG builder."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

from core.dag import build_dag
from core.models import Playbook, PlaybookNode

PLAYBOOK_DIR = Path("playbooks")


def load_playbook(slug: str) -> Playbook:
    path = PLAYBOOK_DIR / f"{slug}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Playbook '{slug}' not found at {path}")
    raw = yaml.safe_load(path.read_text())
    nodes: Dict[str, PlaybookNode] = {}
    for node_id, node_data in raw["nodes"].items():
        nodes[node_id] = PlaybookNode(id=node_id, **node_data)
    playbook = Playbook(
        id=raw.get("id", slug),
        name=raw.get("name", slug),
        description=raw.get("description"),
        entry=raw["entry"],
        nodes=nodes,
    )
    build_dag(playbook)  # validate structure
    return playbook
