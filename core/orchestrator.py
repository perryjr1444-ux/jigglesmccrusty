"""State machine that executes playbooks using agent modules."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List

from agents import commander
from agents import device_remediator, evidence_clerk, hardening_coach, identity_locker, network_steward, platform_reporter
from core.dag import build_dag
from core.models import Case, CaseStatus, Playbook, Task, TaskStatus
from core.policy import PolicyEngine, PolicyViolation
from core.audit import AuditLog

AGENT_ACTIONS: Dict[str, Dict[str, Any]] = {
    "identity_locker": {
        "enforce_account_controls": identity_locker.enforce_account_controls,
        "rotate_credentials": identity_locker.rotate_credentials,
        "prune_tokens": identity_locker.prune_tokens,
    },
    "device_remediator": {
        "quarantine_device": device_remediator.quarantine_device,
        "schedule_patch": device_remediator.schedule_patch,
        "collect_forensics": device_remediator.collect_forensics,
    },
    "network_steward": {
        "reset_router": network_steward.reset_router,
        "rotate_wifi": network_steward.rotate_wifi,
        "lock_carrier_port_out": network_steward.lock_carrier_port_out,
    },
    "evidence_clerk": {
        "collect_mailbox_evidence": evidence_clerk.collect_mailbox_evidence,
        "summarize_alert": evidence_clerk.summarize_alert,
    },
    "platform_reporter": {
        "compile_status_report": platform_reporter.compile_status_report,
        "generate_device_brief": platform_reporter.generate_device_brief,
    },
    "hardening_coach": {
        "recommend_baselines": hardening_coach.recommend_baselines,
        "coach_user": hardening_coach.coach_user,
    },
}


class Orchestrator:
    def __init__(self, policy_engine: PolicyEngine | None = None, audit_log: AuditLog | None = None) -> None:
        self._policy = policy_engine or PolicyEngine.default()
        self._audit = audit_log or AuditLog()
        self._cases: Dict[str, Case] = {}
        self._playbooks: Dict[str, Playbook] = {}

    def ingest_case(self, title: str, description: str, playbook_slug: str, context: Dict[str, Any] | None = None) -> Case:
        playbook = self._get_playbook(playbook_slug)
        case_id = str(uuid.uuid4())
        case = Case(
            id=case_id,
            title=title,
            description=description,
            playbook=playbook_slug,
            context=context or {},
            tasks=self._build_tasks(playbook),
        )
        self._policy.evaluate_case(case)
        self._cases[case_id] = case
        self._audit.append("system", "case_ingested", {"case_id": case_id, "playbook": playbook_slug})
        self._advance_case(case)
        return case

    def approve_task(self, case_id: str, task_id: str, approver: str) -> Task:
        case = self._get_case(case_id)
        task = self._get_task(case, task_id)
        if task.status != TaskStatus.WAITING_APPROVAL:
            raise ValueError(f"Task {task_id} is not awaiting approval")
        task.approvals.append(approver)
        self._audit.append(approver, "task_approved", {"case_id": case_id, "task_id": task_id})
        self._execute_task(case, task)
        self._advance_case(case)
        return task

    def list_cases(self) -> List[Case]:
        return list(self._cases.values())

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return [entry.model_dump() for entry in self._audit.entries]

    def _build_tasks(self, playbook: Playbook) -> List[Task]:
        dag = build_dag(playbook)
        tasks: List[Task] = []
        for node in dag.topological_order(playbook.entry):
            tasks.append(
                Task(
                    id=f"{node.id}-{uuid.uuid4().hex[:8]}",
                    node_id=node.id,
                    name=node.name,
                    agent=node.agent,
                    action=node.action,
                    status=TaskStatus.PENDING,
                    inputs={},
                )
            )
        return tasks

    def _advance_case(self, case: Case) -> None:
        case.status = CaseStatus.OPEN
        completed = True
        for task in case.tasks:
            if task.status == TaskStatus.COMPLETED:
                continue
            if task.status == TaskStatus.WAITING_APPROVAL:
                case.status = CaseStatus.AWAITING_APPROVAL
                completed = False
                break
            self._run_if_ready(case, task)
            if task.status in {TaskStatus.WAITING_APPROVAL, TaskStatus.BLOCKED}:
                completed = False
                break
            if task.status != TaskStatus.COMPLETED:
                completed = False
                break
        if completed:
            case.status = CaseStatus.CLOSED
            case.updated_at = datetime.utcnow()
            self._audit.append("system", "case_closed", {"case_id": case.id})

    def _run_if_ready(self, case: Case, task: Task) -> None:
        if task.status not in {TaskStatus.PENDING, TaskStatus.IN_PROGRESS}:
            return
        task.status = TaskStatus.IN_PROGRESS
        node = self._get_playbook(case.playbook).nodes[task.node_id]
        requires_approval = node.requires_approval
        if requires_approval:
            task.status = TaskStatus.WAITING_APPROVAL
            case.status = CaseStatus.AWAITING_APPROVAL
            task.updated_at = datetime.utcnow()
            self._audit.append(
                "system",
                "task_pending_approval",
                {"case_id": case.id, "task_id": task.id, "agent": task.agent},
            )
            return
        self._execute_task(case, task)

    def _execute_task(self, case: Case, task: Task) -> None:
        handler = AGENT_ACTIONS.get(task.agent, {}).get(task.action)
        if handler is None:
            task.status = TaskStatus.BLOCKED
            task.updated_at = datetime.utcnow()
            self._audit.append(
                "system",
                "task_blocked",
                {"case_id": case.id, "task_id": task.id, "reason": "handler_missing"},
            )
            return
        try:
            inputs = {**case.context, **task.inputs}
            outputs = handler(inputs)
            task.outputs = outputs
            case.context.update({task.action: outputs})
            self._policy.evaluate_task(case, task)
            task.status = TaskStatus.COMPLETED
            task.updated_at = datetime.utcnow()
            case.updated_at = datetime.utcnow()
            self._audit.append(
                "system",
                "task_completed",
                {"case_id": case.id, "task_id": task.id, "agent": task.agent},
            )
        except PolicyViolation as exc:
            task.status = TaskStatus.BLOCKED
            self._audit.append(
                "system",
                "task_blocked",
                {"case_id": case.id, "task_id": task.id, "reason": exc.reason},
            )

    def _get_playbook(self, slug: str) -> Playbook:
        if slug not in self._playbooks:
            self._playbooks[slug] = commander.load_playbook(slug)
        return self._playbooks[slug]

    def _get_case(self, case_id: str) -> Case:
        if case_id not in self._cases:
            raise KeyError(f"Unknown case {case_id}")
        return self._cases[case_id]

    def _get_task(self, case: Case, task_id: str) -> Task:
        for task in case.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Task {task_id} not found")
