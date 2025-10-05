"""OPA-style guardrail DSL."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from core.models import Case, Task


class PolicyViolation(Exception):
    """Raised when a policy rule denies execution."""

    def __init__(self, policy: str, reason: str) -> None:
        super().__init__(f"{policy}: {reason}")
        self.policy = policy
        self.reason = reason


@dataclass
class CasePolicy:
    name: str
    predicate: Callable[[Case], bool]
    message: str


@dataclass
class TaskPolicy:
    name: str
    predicate: Callable[[Case, Task], bool]
    message: str


class PolicyEngine:
    def __init__(self) -> None:
        self._case_policies: List[CasePolicy] = []
        self._task_policies: List[TaskPolicy] = []

    def register_case_policy(self, name: str, predicate: Callable[[Case], bool], message: str) -> None:
        self._case_policies.append(CasePolicy(name, predicate, message))

    def register_task_policy(self, name: str, predicate: Callable[[Case, Task], bool], message: str) -> None:
        self._task_policies.append(TaskPolicy(name, predicate, message))

    def evaluate_case(self, case: Case) -> None:
        for policy in self._case_policies:
            if not policy.predicate(case):
                raise PolicyViolation(policy.name, policy.message)

    def evaluate_task(self, case: Case, task: Task) -> None:
        for policy in self._task_policies:
            if not policy.predicate(case, task):
                raise PolicyViolation(policy.name, policy.message)

    @classmethod
    def default(cls) -> "PolicyEngine":
        engine = cls()
        engine.register_case_policy(
            "case-title-present",
            lambda case: bool(case.title.strip()),
            "Case title is required.",
        )
        engine.register_task_policy(
            "outputs-after-approval",
            lambda case, task: not task.approvals or bool(task.outputs),
            "Approved tasks must emit outputs before completion.",
        )
        return engine
