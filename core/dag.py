"""Lightweight DAG utilities for playbook execution."""
from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Set

from core.models import Playbook, PlaybookNode


class Dag:
    def __init__(self, nodes: Dict[str, PlaybookNode]) -> None:
        self.nodes = nodes
        self._validate()

    def _validate(self) -> None:
        for node_id, node in self.nodes.items():
            for edge in node.next:
                if edge not in self.nodes:
                    raise ValueError(f"Playbook references unknown node '{edge}' from '{node_id}'")
        if self._has_cycle():
            raise ValueError("Playbook contains a cycle; DAG execution is not possible")

    def _has_cycle(self) -> bool:
        visited: Set[str] = set()
        recursion: Set[str] = set()

        def visit(node_id: str) -> bool:
            if node_id in recursion:
                return True
            if node_id in visited:
                return False
            recursion.add(node_id)
            for child in self.nodes[node_id].next:
                if visit(child):
                    return True
            recursion.remove(node_id)
            visited.add(node_id)
            return False

        return any(visit(node_id) for node_id in self.nodes)

    def topological_order(self, entry: str) -> List[PlaybookNode]:
        if entry not in self.nodes:
            raise KeyError(f"Entry node '{entry}' not found")
        indegree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        for node in self.nodes.values():
            for child in node.next:
                indegree[child] += 1
        if indegree[entry] != 0:
            raise ValueError(f"Entry node '{entry}' has unmet dependencies")

        queue: deque[str] = deque([entry])
        visited: Set[str] = {entry}
        ordered: List[PlaybookNode] = []

        while queue:
            node_id = queue.popleft()
            ordered.append(self.nodes[node_id])
            for child in self.nodes[node_id].next:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
                    visited.add(child)

        if len(ordered) != len(self.nodes):
            missing = set(self.nodes) - {node.id for node in ordered}
            raise ValueError(f"Graph contains unreachable nodes: {sorted(missing)}")
        return ordered

    def children_of(self, node_id: str) -> Iterable[PlaybookNode]:
        for child in self.nodes[node_id].next:
            yield self.nodes[child]


def build_dag(playbook: Playbook) -> Dag:
    return Dag(playbook.nodes)
