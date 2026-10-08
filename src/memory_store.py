"""
ServiceFlow — Week 6 Persistent Memory Store
===============================================
One justified persistent-memory use case: minimal CASE HISTORY per customer,
kept across sessions so the agent can notice likely duplicate reports and
give support staff continuity — nothing more.

Data-minimisation decision (see the Memory Design and Data Handling Note):
the raw customer message is NEVER stored here. Only a small structured
summary is kept: customer_id, category, outcome, ticket_id, timestamp.
The full message text lives only in the ephemeral Week 5 AgentState/trace
for the duration of one run and is discarded afterwards.

Backed by an in-memory dict for this demonstration — a real deployment
would back this with a database, but the access pattern (keyed by
customer_id, append-only, with explicit retention pruning and deletion)
would stay identical.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class CaseRecord:
    customer_id: str
    category: str
    outcome: str  # resolved_rag | resolved_outage | ticket_created | waiting_for_customer | escalated_max_iterations
    ticket_id: Optional[str]
    timestamp: str  # ISO 8601, UTC


class CaseHistoryStore:
    def __init__(self):
        self._store: dict[str, list[CaseRecord]] = {}

    # --- write path -----------------------------------------------------
    def record_interaction(self, customer_id: str, category: str, outcome: str,
                            ticket_id: Optional[str] = None) -> CaseRecord:
        record = CaseRecord(customer_id=customer_id, category=category, outcome=outcome,
                             ticket_id=ticket_id, timestamp=datetime.now(timezone.utc).isoformat())
        self._store.setdefault(customer_id, []).append(record)
        return record

    # --- read path (informational only — see agent_with_memory.py for
    #     how this is used WITHOUT silently blocking any decision) -------
    def get_recent_history(self, customer_id: str, within_hours: int = 24) -> list[CaseRecord]:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
        return [r for r in self._store.get(customer_id, [])
                if datetime.fromisoformat(r.timestamp) >= cutoff]

    def find_possible_duplicate(self, customer_id: str, category: str,
                                 within_hours: int = 24) -> Optional[CaseRecord]:
        """Returns the most recent matching prior case, or None. This is a HINT
        for a human reviewer — it never prevents or auto-approves a ticket."""
        recent = self.get_recent_history(customer_id, within_hours)
        matches = [r for r in recent if r.category == category
                   and r.outcome in ("ticket_created", "escalated_max_iterations")]
        return matches[-1] if matches else None

    # --- retention / deletion (see Data Handling Note) -------------------
    def purge_older_than(self, hours: int) -> int:
        """Retention enforcement: drop any record older than `hours`. Returns count removed."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        removed = 0
        for cid in list(self._store):
            before = len(self._store[cid])
            self._store[cid] = [r for r in self._store[cid] if datetime.fromisoformat(r.timestamp) >= cutoff]
            removed += before - len(self._store[cid])
            if not self._store[cid]:
                del self._store[cid]
        return removed

    def delete_customer_history(self, customer_id: str) -> bool:
        """Right-to-deletion: fully erase one customer's case history on request."""
        return self._store.pop(customer_id, None) is not None
