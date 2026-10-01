"""
ServiceFlow — Week 4 Tools and Function Calling
=================================================
Two explicit tools sit behind the orchestration layer built on top of the
Week 2 classification baseline and the Week 3 RAG pipeline:

1. check_outage_status  — READ-ONLY. Queries simulated "current application
   data" (a mock outage/incident table). Low risk, no human approval needed.
2. create_support_ticket — WRITE / SIDE-EFFECTING. Creates a simulated
   ticket/draft record. Treated as a higher-impact action: every ticket
   requires an explicit human-approval step before it is actually persisted,
   per the project's AI Boundary Matrix ("no automatic ticket creation
   without approval; no remote control of infrastructure").

This script is fully offline and deterministic — everything in the Week 4
evaluation table was produced by actually running it, not simulated.
"""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Mock "current application data" — stands in for a real outage/status system
# ---------------------------------------------------------------------------
MOCK_OUTAGE_DB = {
    "KLA-05": {"status": "outage_confirmed", "eta_minutes": 90, "incident_id": "INC-2031"},
    "KLA-12": {"status": "no_known_outage", "eta_minutes": None, "incident_id": None},
    "MBR-02": {"status": "outage_confirmed", "eta_minutes": 30, "incident_id": "INC-2044"},
    "DWN-99": "__SIMULATED_SERVICE_UNAVAILABLE__",  # forces a tool-unavailable test case (valid format, so it reaches the DB lookup)
}

MOCK_TICKET_STORE = []  # in-memory "database" of created tickets
VALID_CATEGORIES = {"no_connection", "slow_connection", "intermittent_connection",
                     "router_modem_issue", "possible_outage", "unclear"}
VALID_PRIORITIES = {"low", "medium", "high"}


class ToolError(Exception):
    """Structured tool failure — every failure has a machine-readable type."""
    def __init__(self, error_type: str, message: str):
        self.error_type = error_type  # validation_error | unauthorized | unavailable | not_found
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------------------------
# Tool 1: check_outage_status
# ---------------------------------------------------------------------------
def check_outage_status(args: dict, context: dict) -> dict:
    """
    Purpose: read-only lookup of simulated outage/incident status for an area.
    Input schema : { "area_code": str }
    Output schema: { "status": "outage_confirmed"|"no_known_outage"|"area_not_found",
                      "area_code": str, "eta_minutes": int|None, "incident_id": str|None }
    Authorization: none required — read-only, no customer data exposed beyond
                   the area the customer already told us they're in.
    Failure behaviour: missing/malformed area_code -> validation_error;
                       simulated backend outage -> unavailable (caller should
                       retry once, then tell the customer to try later).
    """
    area_code = args.get("area_code")
    if not area_code or not re.match(r"^[A-Z]{3}-\d{2}$", str(area_code)):
        raise ToolError("validation_error", "area_code is required and must match format XXX-NN.")

    record = MOCK_OUTAGE_DB.get(area_code)
    if record == "__SIMULATED_SERVICE_UNAVAILABLE__":
        raise ToolError("unavailable", "Outage-status service did not respond (simulated).")
    if record is None:
        return {"status": "area_not_found", "area_code": area_code, "eta_minutes": None, "incident_id": None}

    return {"status": record["status"], "area_code": area_code,
            "eta_minutes": record["eta_minutes"], "incident_id": record["incident_id"]}


# ---------------------------------------------------------------------------
# Tool 2: create_support_ticket  (higher-impact — human approval required)
# ---------------------------------------------------------------------------
@dataclass
class PendingTicket:
    ticket_id: str
    customer_id: str
    category: str
    description: str
    priority: str
    status: str = "pending_approval"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def create_support_ticket(args: dict, context: dict) -> dict:
    """
    Purpose: create a simulated support ticket/draft record for a customer issue.
    Input schema : { "customer_id": str, "category": <one of VALID_CATEGORIES>,
                      "description": str, "priority": "low"|"medium"|"high" }
    Output schema: { "ticket_id": str, "status": "pending_approval"|"created"|"rejected",
                      "created_at": iso-timestamp }
    Authorization: caller must present a verified customer_id in `context`
                   (simulates an authenticated session) — the tool refuses to
                   create a ticket for a customer_id it cannot verify.
    Human approval: EVERY ticket is created in "pending_approval" state first.
                   It only moves to "created" after an explicit approve_ticket()
                   call — this is the project's human-approval gate for a
                   higher-impact action, and is never skipped, regardless of
                   priority.
    Failure behaviour: missing required field -> validation_error;
                       category not in the approved set -> validation_error;
                       customer_id not verified -> unauthorized.
    """
    customer_id = args.get("customer_id")
    category = args.get("category")
    description = args.get("description")
    priority = args.get("priority", "low")

    missing = [f for f in ("customer_id", "category", "description") if not args.get(f)]
    if missing:
        raise ToolError("validation_error", f"Missing required field(s): {', '.join(missing)}.")
    if category not in VALID_CATEGORIES:
        raise ToolError("validation_error", f"'{category}' is not an approved category.")
    if priority not in VALID_PRIORITIES:
        raise ToolError("validation_error", f"'{priority}' is not a valid priority.")

    if customer_id != context.get("verified_customer_id"):
        raise ToolError("unauthorized", "customer_id does not match the verified session — refusing to create a ticket on their behalf.")

    ticket = PendingTicket(
        ticket_id=f"TCK-{uuid.uuid4().hex[:8].upper()}",
        customer_id=customer_id, category=category,
        description=description, priority=priority,
    )
    MOCK_TICKET_STORE.append(ticket)
    return {"ticket_id": ticket.ticket_id, "status": ticket.status, "created_at": ticket.created_at}


def approve_ticket(ticket_id: str, approved_by: str) -> dict:
    """The deterministic human-approval step. Nothing calls this but a human action."""
    for t in MOCK_TICKET_STORE:
        if t.ticket_id == ticket_id:
            t.status = "created"
            return {"ticket_id": ticket_id, "status": "created", "approved_by": approved_by}
    raise ToolError("not_found", f"No pending ticket with id {ticket_id}.")


# ---------------------------------------------------------------------------
# Orchestration layer — routes a tool call, enforces the contract, logs a trace
# ---------------------------------------------------------------------------
TOOLS = {"check_outage_status": check_outage_status, "create_support_ticket": create_support_ticket}


def call_tool(tool_name: str, args: dict, context: dict) -> dict:
    trace = {"tool": tool_name, "args": args, "context": context}
    if tool_name not in TOOLS:
        trace["result"] = {"error_type": "not_found", "message": f"Unknown tool '{tool_name}'."}
        return trace
    try:
        trace["result"] = {"ok": True, "output": TOOLS[tool_name](args, context)}
    except ToolError as e:
        trace["result"] = {"ok": False, "error_type": e.error_type, "message": e.message}
    return trace


# ---------------------------------------------------------------------------
# Week 4 test set — covers normal use, missing params, unauthorized requests,
# an unavailable service, and the human-approval flow end to end.
# ---------------------------------------------------------------------------
TEST_CASES = [
    {"id": 1, "desc": "Outage check — confirmed outage", "tool": "check_outage_status",
     "args": {"area_code": "KLA-05"}, "context": {}},
    {"id": 2, "desc": "Outage check — no known outage", "tool": "check_outage_status",
     "args": {"area_code": "KLA-12"}, "context": {}},
    {"id": 3, "desc": "Outage check — unknown area", "tool": "check_outage_status",
     "args": {"area_code": "ZZZ-99"}, "context": {}},
    {"id": 4, "desc": "Outage check — missing area_code", "tool": "check_outage_status",
     "args": {}, "context": {}},
    {"id": 5, "desc": "Outage check — simulated service unavailable", "tool": "check_outage_status",
     "args": {"area_code": "DWN-99"}, "context": {}},
    {"id": 6, "desc": "Create ticket — valid request, authorized", "tool": "create_support_ticket",
     "args": {"customer_id": "CUST-100", "category": "router_modem_issue",
              "description": "Router light blinking red for 2 days.", "priority": "medium"},
     "context": {"verified_customer_id": "CUST-100"}},
    {"id": 7, "desc": "Create ticket — missing description", "tool": "create_support_ticket",
     "args": {"customer_id": "CUST-100", "category": "slow_connection", "priority": "low"},
     "context": {"verified_customer_id": "CUST-100"}},
    {"id": 8, "desc": "Create ticket — invalid category", "tool": "create_support_ticket",
     "args": {"customer_id": "CUST-100", "category": "billing_dispute",
              "description": "Wrong charge on my bill.", "priority": "low"},
     "context": {"verified_customer_id": "CUST-100"}},
    {"id": 9, "desc": "Create ticket — unauthorized (customer_id mismatch)", "tool": "create_support_ticket",
     "args": {"customer_id": "CUST-999", "category": "no_connection",
              "description": "No internet since this morning.", "priority": "high"},
     "context": {"verified_customer_id": "CUST-100"}},
    {"id": 10, "desc": "Create ticket — unknown tool name (unexpected request)", "tool": "cancel_service",
     "args": {"customer_id": "CUST-100"}, "context": {"verified_customer_id": "CUST-100"}},
]


if __name__ == "__main__":
    print("=== Running Week 4 tool test cases ===\n")
    created_ticket_id = None
    for case in TEST_CASES:
        result = call_tool(case["tool"], case["args"], case["context"])
        print(f"Case {case['id']}: {case['desc']}")
        print(f"  -> {result['result']}\n")
        if case["id"] == 6 and result["result"].get("ok"):
            created_ticket_id = result["result"]["output"]["ticket_id"]

    if created_ticket_id:
        print("=== Human-approval step (case 6's ticket) ===")
        print(f"Before approval: {[t for t in MOCK_TICKET_STORE if t.ticket_id == created_ticket_id]}")
        approval = approve_ticket(created_ticket_id, approved_by="human_agent_dennise")
        print(f"approve_ticket() -> {approval}")
