"""Deterministic recovery handling for Phase 5."""

from __future__ import annotations

from typing import Any

from governance.checkpoint_manager import CheckpointManager
from governance.dead_letter_queue import DeadLetterQueue
from governance.failure_taxonomy import recommended_action
from memory.quarantine_store import QuarantineStore


class RecoveryManager:
    """Simple recovery decisions without autonomous retry loops."""

    MAX_RETRY_ATTEMPTS = 1

    def __init__(
        self,
        *,
        checkpoint_manager: CheckpointManager | None = None,
        quarantine_store: QuarantineStore | None = None,
        dead_letter_queue: DeadLetterQueue | None = None,
    ):
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
        self.quarantine_store = quarantine_store or QuarantineStore()
        self.dead_letter_queue = dead_letter_queue or DeadLetterQueue()

    def can_retry(self, *, retry_count: int) -> bool:
        return retry_count < self.MAX_RETRY_ATTEMPTS

    def can_fallback(self, failure_class: str) -> bool:
        return recommended_action(failure_class) == "fallback"

    def can_resume(self, run_id: str) -> bool:
        return self.checkpoint_manager.latest_for_run(run_id) is not None

    def can_rollback(self, run_id: str) -> bool:
        checkpoints = self.checkpoint_manager.list_for_run(run_id)
        return len(checkpoints) >= 1

    def quarantine_output(
        self,
        *,
        run_id: str,
        payload: dict[str, Any],
        reason: str,
        failure_class: str,
        accountability_owner: str,
    ) -> dict[str, Any]:
        return self.quarantine_store.add(
            run_id=run_id,
            payload=payload,
            reason=reason,
            failure_class=failure_class,
            accountability_owner=accountability_owner,
        )

    def write_dead_letter(
        self,
        *,
        run_id: str,
        task_id: str,
        agent_id: str,
        skill_id: str,
        failure_class: str,
        reason: str,
        accountability_owner: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.dead_letter_queue.append(
            run_id=run_id,
            task_id=task_id,
            agent_id=agent_id,
            skill_id=skill_id,
            failure_class=failure_class,
            reason=reason,
            accountability_owner=accountability_owner,
            payload=payload,
        )

    def handle_failure(
        self,
        *,
        run_id: str,
        context: dict[str, Any],
        step_result: dict[str, Any],
        failure_class: str,
        reason: str,
    ) -> dict[str, Any]:
        """Route a failure to quarantine, rollback, or dead-letter."""
        action = recommended_action(failure_class)
        payload = {
            "step_result": step_result,
            "reason": reason,
            "failure_class": failure_class,
        }

        result: dict[str, Any] = {
            "failure_class": failure_class,
            "recommended_action": action,
            "reason": reason,
        }

        if action in {"quarantine", "halt"}:
            quarantine_entry = self.quarantine_output(
                run_id=run_id,
                payload=payload,
                reason=reason,
                failure_class=failure_class,
                accountability_owner=context.get("accountability_owner", ""),
            )
            result["quarantine_entry"] = quarantine_entry

        if action == "dead_letter" or (
            action == "rollback" and not self.can_rollback(run_id)
        ):
            dead_letter = self.write_dead_letter(
                run_id=run_id,
                task_id=step_result.get("skill_id", "unknown"),
                agent_id=step_result.get("agent_id", "unknown"),
                skill_id=step_result.get("skill_id", "unknown"),
                failure_class=failure_class,
                reason=reason,
                accountability_owner=context.get("accountability_owner", ""),
                payload=payload,
            )
            result["dead_letter_entry"] = dead_letter
            result["halted"] = True

        return result

    def resume_state(self, checkpoint: dict[str, Any]) -> dict[str, Any]:
        self.checkpoint_manager.update_status(checkpoint["checkpoint_id"], "resumed")
        return {
            "status": "resumed",
            "checkpoint_id": checkpoint["checkpoint_id"],
            "agent_context": checkpoint.get("agent_context", {}),
            "completed_steps": checkpoint.get("completed_steps", []),
            "current_step": checkpoint.get("current_step"),
            "output_refs": checkpoint.get("output_refs", {}),
        }

    def rollback_state(self, checkpoint: dict[str, Any]) -> dict[str, Any]:
        self.checkpoint_manager.update_status(checkpoint["checkpoint_id"], "rolled_back")
        return {
            "status": "rolled_back",
            "checkpoint_id": checkpoint["checkpoint_id"],
            "agent_context": checkpoint.get("agent_context", {}),
            "completed_steps": checkpoint.get("completed_steps", []),
            "current_step": checkpoint.get("current_step"),
            "output_refs": checkpoint.get("output_refs", {}),
        }
