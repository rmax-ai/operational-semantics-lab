"""Append-only provenance ledger with hash chaining.

Records business-level events. Each event includes a hash of the previous
event in the same aggregate, providing tamper-evident chaining.
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventType(str, Enum):
    """All event types recorded by the provenance ledger."""

    EVIDENCE_REGISTERED = "EVIDENCE_REGISTERED"
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    PROPOSAL_VALIDATED = "PROPOSAL_VALIDATED"
    POLICY_EVALUATED = "POLICY_EVALUATED"
    APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_REJECTED = "APPROVAL_REJECTED"
    APPROVAL_INVALIDATED = "APPROVAL_INVALIDATED"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_SUCCEEDED = "EXECUTION_SUCCEEDED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"


class LedgerEvent:
    """A single event in the provenance ledger."""

    def __init__(
        self,
        event_type: EventType | str,
        actor_id: str,
        aggregate_id: str,
        related_ids: dict[str, list[str]] | None = None,
        payload: dict[str, Any] | None = None,
        previous_event_hash: str = "",
    ) -> None:
        self.event_id = f"evt-{aggregate_id}-{_utcnow().timestamp():.6f}"
        self.event_type = event_type.value if isinstance(event_type, EventType) else event_type
        self.timestamp = _utcnow()
        self.actor_id = actor_id
        self.aggregate_id = aggregate_id
        self.related_ids = related_ids or {}
        self.payload = payload or {}
        self.previous_event_hash = previous_event_hash
        self.event_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute a deterministic hash of this event's contents."""
        canonical = json.dumps(
            {
                "event_id": self.event_id,
                "event_type": self.event_type,
                "timestamp": self.timestamp.isoformat(),
                "actor_id": self.actor_id,
                "aggregate_id": self.aggregate_id,
                "related_ids": self.related_ids,
                "payload": self.payload,
                "previous_event_hash": self.previous_event_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary for storage."""
        return {
            "id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "aggregate_id": self.aggregate_id,
            "related_ids": self.related_ids,
            "payload": self.payload,
            "previous_event_hash": self.previous_event_hash,
            "event_hash": self.event_hash,
        }


class ProvenanceLedger:
    """Append-only ledger recording business events.

    Events are stored in memory and optionally persisted to the database.
    """

    def __init__(self) -> None:
        self._events: dict[str, LedgerEvent] = {}
        self._aggregates: dict[str, list[LedgerEvent]] = {}

    def record(self, event: LedgerEvent) -> LedgerEvent:
        """Record an event in the ledger.

        Automatically chains to the previous event in the same aggregate.
        """
        # Find previous event hash
        if event.aggregate_id in self._aggregates:
            prev_events = self._aggregates[event.aggregate_id]
            if prev_events:
                event.previous_event_hash = prev_events[-1].event_hash
                # Recompute hash with correct previous hash
                event.event_hash = event._compute_hash()

        # Store event
        self._events[event.event_id] = event
        if event.aggregate_id not in self._aggregates:
            self._aggregates[event.aggregate_id] = []
        self._aggregates[event.aggregate_id].append(event)
        return event

    def get_event(self, event_id: str) -> LedgerEvent | None:
        """Get a single event by ID."""
        return self._events.get(event_id)

    def get_aggregate_events(self, aggregate_id: str) -> list[LedgerEvent]:
        """Get all events for an aggregate, in chain order."""
        return list(self._aggregates.get(aggregate_id, []))

    def get_events_by_type(self, event_type: str) -> list[LedgerEvent]:
        """Get all events of a specific type."""
        return [
            e for e in self._events.values() if e.event_type == event_type
        ]

    def verify_chain(self, aggregate_id: str) -> bool:
        """Verify the hash chain integrity for an aggregate.

        Returns True if the chain is valid.
        """
        events = self._aggregates.get(aggregate_id, [])
        if not events:
            return True

        prev_hash = ""
        for event in events:
            stored_hash = event.event_hash
            event.event_hash = ""  # Temporarily clear to recompute
            expected = event._compute_hash()
            event.event_hash = stored_hash

            if expected != stored_hash:
                return False
            if event.previous_event_hash != prev_hash:
                return False
            prev_hash = stored_hash

        return True

    def all_events(self) -> list[LedgerEvent]:
        """Get all events (sorted by aggregate then timestamp)."""
        return sorted(self._events.values(), key=lambda e: e.timestamp)

    def clear(self) -> None:
        """Clear all events (for testing)."""
        self._events.clear()
        self._aggregates.clear()
