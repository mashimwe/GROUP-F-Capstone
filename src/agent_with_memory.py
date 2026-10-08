"""
ServiceFlow — Week 6 Memory-Aware Agent Wrapper
==================================================
Wraps Week 5's run_agent() with the persistent CaseHistoryStore. Nothing in
Week 5's agent.py loop, bounds, or stop conditions changes except the single
additive line noted in agent.py's create_support_ticket branch.

Two memory touch-points, both OUTSIDE the agent's own decision loop:
  1. BEFORE a run: check for a likely duplicate case and pass it in as
     context (a hint only — see find_possible_duplicate's docstring).
  2. AFTER a run: record a minimal outcome summary — never the raw message.

This keeps the separation the State Model document describes: SESSION STATE
(AgentState, ephemeral, one run) vs PERSISTENT MEMORY (CaseHistoryStore,
durable, across runs) stay two distinct objects with two distinct lifetimes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from agent import run_agent, classify
from memory_store import CaseHistoryStore


def outcome_of(state) -> str:
    if state.stop_reason == "stop_resolved":
        if state.outage_result and state.outage_result.get("status") == "outage_confirmed" and not state.rag_attempted:
            return "resolved_outage"
        return "resolved_rag"
    if state.stop_reason == "stop_handoff_pending_approval":
        return "ticket_created"
    if state.stop_reason == "stop_waiting_for_customer":
        return "waiting_for_customer"
    return "escalated_max_iterations"


def run_agent_with_memory(message: str, context: dict, store: CaseHistoryStore, within_hours: int = 24):
    customer_id = context.get("verified_customer_id")

    # Touch-point 1: a lightweight pre-check for a likely duplicate. This uses
    # the SAME classify() the agent itself will call again — it is cheap and
    # deterministic, so calling it twice costs nothing but a few milliseconds
    # and keeps this wrapper from reaching into the agent's internal state.
    likely_category = classify(message)["category"]
    duplicate = store.find_possible_duplicate(customer_id, likely_category, within_hours)

    run_context = dict(context)  # never mutate the caller's dict
    if duplicate:
        run_context["possible_duplicate_of"] = duplicate.ticket_id or "a prior escalation (no ticket id)"

    state = run_agent(message, run_context)

    # Touch-point 2: record the minimal outcome summary only — no message text.
    store.record_interaction(customer_id, state.category, outcome_of(state), state.ticket_id)

    return state, duplicate


if __name__ == "__main__":
    store = CaseHistoryStore()
    ticket_message = ("My smart TV app drops out for exactly one second every night at midnight, "
                       "nothing else does this, already tried the standard fixes, please escalate")
    other_category_message = "My internet is really slow every evening when streaming video."

    print("=== Interaction 1: first-time report, no history yet ===")
    s1, dup1 = run_agent_with_memory(ticket_message, {"verified_customer_id": "CUST-200"}, store)
    print(f"Outcome: {outcome_of(s1)} | ticket_id: {s1.ticket_id} | duplicate flagged: {dup1}")

    print("\n=== Interaction 2: SAME customer, SAME category, 2 hours later (simulated) — expect duplicate flag ===")
    s2, dup2 = run_agent_with_memory(ticket_message, {"verified_customer_id": "CUST-200"}, store)
    print(f"Outcome: {outcome_of(s2)} | ticket_id: {s2.ticket_id} | duplicate flagged: {dup2}")
    if s2.ticket_id:
        from tools import MOCK_TICKET_STORE
        matching = [t for t in MOCK_TICKET_STORE if t.ticket_id == s2.ticket_id][0]
        print(f"Ticket description seen by the human reviewer: \"{matching.description}\"")

    print("\n=== Interaction 3: SAME customer, DIFFERENT category — expect NO duplicate flag ===")
    s3, dup3 = run_agent_with_memory(other_category_message, {"verified_customer_id": "CUST-200"}, store)
    print(f"Outcome: {outcome_of(s3)} | duplicate flagged: {dup3}")

    print("\n=== Data handling: customer requests deletion of their case history ===")
    before = store.get_recent_history("CUST-200", within_hours=24)
    print(f"Records before deletion: {len(before)}")
    store.delete_customer_history("CUST-200")
    after = store.get_recent_history("CUST-200", within_hours=24)
    print(f"Records after delete_customer_history('CUST-200'): {len(after)}")
