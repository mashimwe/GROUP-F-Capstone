"""
ServiceFlow — Week 5 Bounded Agent Workflow
=============================================
Implements one goal-directed, multi-step workflow that chooses among
approved next actions and stops safely, built entirely on top of already-
tested Week 3 (RAG retrieval) and Week 4 (tools) components.

Loop: Sense/Context -> Plan/Decide -> Act/Tool -> Observe -> Stop/Re-plan

Goal
----
Given one customer message (+ known account context), resolve it end to end:
classify -> (check outage if relevant) -> ground an answer in the knowledge
base -> if still unresolved, create a (pending) support ticket -> always
stop at a safe, defined point rather than looping indefinitely.

Engineering note on classification
-----------------------------------
Week 2 already tested a Gemini-backed classifier; Week 3 already tested the
RAG retriever. This week is about the agent LOOP and its bounds, not about
re-testing either of those. So the "plan" step here reuses the real, offline
RagIndex from Week 3 unchanged, but stands in a lightweight deterministic
keyword classifier in place of Week 2's Gemini call, purely so every trace
in this document is fully reproducible offline without an API key. The
production version plugs classify_problem() from serviceflow_baseline.py
into the same slot (see classify() below).
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from rag_pipeline import load_corpus, RagIndex          # Week 3, unchanged
from tools import call_tool                              # Week 4, unchanged

MAX_ITERATIONS = 6
MAX_TOOL_RETRIES = 1
RESOLUTION_THRESHOLD = 0.15  # same similarity floor used in Week 3's evaluation

APPROVED_TOOLS = ["classify", "check_outage_status", "retrieve_and_answer",
                   "ask_clarifying_question", "create_support_ticket"]


# ---------------------------------------------------------------------------
# Week-5-only stand-in for the Week 2 classifier (see module docstring)
# ---------------------------------------------------------------------------
KEYWORD_RULES = [
    ("possible_outage", ["outage", "everyone", "neighbour", "neighbor", "area"]),
    ("no_connection", ["no internet", "completely down", "nothing works", "no wifi", "dead"]),
    ("intermittent_connection", ["drops", "keeps dropping", "comes back", "on and off"]),
    ("router_modem_issue", ["router", "modem", "light", "blinking"]),
    ("slow_connection", ["slow", "buffering", "streaming"]),
]

def classify(message: str) -> dict:
    text = message.lower()
    for category, keywords in KEYWORD_RULES:
        if any(k in text for k in keywords):
            return {"category": category, "confidence": "medium"}
    return {"category": "unclear", "confidence": "low"}


# ---------------------------------------------------------------------------
# Agent state — the "Context" the Plan step senses on every iteration
# ---------------------------------------------------------------------------
@dataclass
class AgentState:
    message: str
    context: dict
    iteration: int = 0
    category: Optional[str] = None
    outage_checked: bool = False
    outage_result: Optional[dict] = None
    outage_retry_count: int = 0
    rag_attempted: bool = False
    rag_answer: Optional[dict] = None
    resolved: bool = False
    clarification_asked: bool = False
    ticket_id: Optional[str] = None
    stopped: bool = False
    stop_reason: Optional[str] = None
    trace: list = field(default_factory=list)

    def log(self, action, detail):
        self.trace.append({"iteration": self.iteration, "action": action, "detail": detail})


# ---------------------------------------------------------------------------
# Plan/Decide — pure function of state; this IS the bounded-autonomy policy
# ---------------------------------------------------------------------------
def plan_next_action(state: AgentState) -> str:
    if state.category is None:
        return "classify"

    if state.category == "possible_outage" and not state.outage_checked:
        return "check_outage_status"

    if state.category == "possible_outage" and state.outage_result and \
       state.outage_result.get("status") in ("outage_confirmed", "no_known_outage") and \
       not state.rag_attempted and state.outage_result.get("status") == "outage_confirmed":
        return "stop_resolved"  # confirmed outage IS the answer, nothing more to do

    if state.category == "unclear" and not state.clarification_asked:
        return "ask_clarifying_question"
    if state.category == "unclear" and state.clarification_asked:
        return "stop_waiting_for_customer"

    if not state.rag_attempted:
        return "retrieve_and_answer"

    if state.resolved:
        return "stop_resolved"

    if state.ticket_id is None:
        return "create_support_ticket"

    return "stop_handoff_pending_approval"


# ---------------------------------------------------------------------------
# Act — executes exactly one approved action against Week 3/Week 4 components
# ---------------------------------------------------------------------------
_rag_index = None
def get_rag_index():
    global _rag_index
    if _rag_index is None:
        _rag_index = RagIndex(load_corpus())
    return _rag_index


def act(action: str, state: AgentState):
    if action == "classify":
        result = classify(state.message)
        state.category = result["category"]
        state.log("classify", result)

    elif action == "check_outage_status":
        area_code = state.context.get("area_code")
        result = call_tool("check_outage_status", {"area_code": area_code}, state.context)
        state.outage_checked_this_step = True
        if result["result"].get("ok"):
            state.outage_checked = True
            state.outage_result = result["result"]["output"]
            state.log("check_outage_status", result["result"])
        else:
            state.outage_retry_count += 1
            state.log("check_outage_status_failed", result["result"])
            if state.outage_retry_count > MAX_TOOL_RETRIES:
                state.outage_checked = True  # give up retrying, move on
                state.outage_result = {"status": "unavailable_after_retry"}

    elif action == "retrieve_and_answer":
        index = get_rag_index()
        hits = index.retrieve(state.message, k=3)
        state.rag_attempted = True
        if hits and hits[0]["score"] >= RESOLUTION_THRESHOLD:
            state.resolved = True
            state.rag_answer = {"top_source": hits[0]["id"], "title": hits[0]["title"], "score": hits[0]["score"]}
        else:
            state.resolved = False
            state.rag_answer = {"top_source": None, "note": "no chunk cleared the resolution threshold"}
        state.log("retrieve_and_answer", {"hits": hits, "resolved": state.resolved})

    elif action == "ask_clarifying_question":
        state.clarification_asked = True
        state.log("ask_clarifying_question", {"question": "Could you tell me more about what's happening with your connection?"})

    elif action == "create_support_ticket":
        priority = "high" if state.category in ("no_connection", "possible_outage") else "medium"
        # Week 6 addition: if the memory layer (agent_with_memory.py) flagged a
        # likely duplicate before this run started, surface it to the human
        # reviewer in the ticket description. This is the ONLY line Week 6 adds
        # to Week 5's agent.py — it never blocks or auto-resolves anything;
        # the ticket is still created and still requires approval either way.
        description = state.message
        duplicate_of = state.context.get("possible_duplicate_of")
        if duplicate_of:
            description = f"[Possible duplicate of {duplicate_of} — see case history] {description}"
        args = {"customer_id": state.context.get("verified_customer_id"), "category": state.category,
                "description": description, "priority": priority}
        result = call_tool("create_support_ticket", args, state.context)
        if result["result"].get("ok"):
            state.ticket_id = result["result"]["output"]["ticket_id"]
        state.log("create_support_ticket", result["result"])

    return action


TERMINAL_ACTIONS = {"stop_resolved", "stop_waiting_for_customer", "stop_handoff_pending_approval"}


# ---------------------------------------------------------------------------
# The bounded loop itself: Sense -> Plan -> Act -> Observe -> Stop/Re-plan
# ---------------------------------------------------------------------------
def run_agent(message: str, context: dict) -> AgentState:
    state = AgentState(message=message, context=context)
    while state.iteration < MAX_ITERATIONS and not state.stopped:
        state.iteration += 1
        action = plan_next_action(state)  # Plan/Decide senses state implicitly
        if action in TERMINAL_ACTIONS:
            state.stopped = True
            state.stop_reason = action
            state.log(action, {})
            break
        act(action, state)  # Act/Tool, then Observe happens inside act() via state mutation

    if not state.stopped:
        state.stopped = True
        state.stop_reason = "max_iterations_reached"
        state.log("stop_max_iterations_reached", {"iterations": state.iteration})

    return state


# ---------------------------------------------------------------------------
# Three (here: four) execution traces, including one failure/recovery case
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scenarios = [
        {
            "name": "Trace 1 — resolved directly by grounded RAG answer",
            "message": "My connection keeps dropping every few minutes, then comes back.",
            "context": {"verified_customer_id": "CUST-100"},
        },
        {
            "name": "Trace 2 — resolved by the outage-status tool alone",
            "message": "Is there an outage in my area? My neighbours say theirs is down too.",
            "context": {"verified_customer_id": "CUST-100", "area_code": "KLA-05"},
        },
        {
            "name": "Trace 3 — FAILURE then RECOVERY: outage tool unavailable, retried, then falls back to RAG",
            "message": "Is there an outage? My connection just went completely dead.",
            "context": {"verified_customer_id": "CUST-100", "area_code": "DWN-99"},
        },
        {
            "name": "Trace 4 — unresolved after RAG, ends in a pending ticket (human hand-off)",
            "message": "My smart TV app drops out for exactly one second every night at midnight, nothing else does this, already tried the standard fixes, please escalate",
            "context": {"verified_customer_id": "CUST-100"},
        },
    ]

    for sc in scenarios:
        print(f"\n{'='*70}\n{sc['name']}\nInput: {sc['message']}\n{'='*70}")
        result = run_agent(sc["message"], sc["context"])
        for step in result.trace:
            print(f"  [{step['iteration']}] {step['action']}: {step['detail']}")
        print(f"STOPPED after {result.iteration} iteration(s) — reason: {result.stop_reason}")
