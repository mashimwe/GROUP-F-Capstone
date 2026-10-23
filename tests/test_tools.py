import pytest

import tools


def test_outage_confirmed():
    r = tools.call_tool("check_outage_status", {"area_code": "KLA-05"}, {})["result"]
    assert r["ok"] and r["output"]["status"] == "outage_confirmed" and r["output"]["eta_minutes"] == 90


@pytest.mark.parametrize("args,err", [({}, "validation_error"), ({"area_code": "kla5"}, "validation_error"), ({"area_code": "DWN-99"}, "unavailable")])
def test_outage_errors_are_typed(args, err):
    r = tools.call_tool("check_outage_status", args, {})["result"]
    assert r["ok"] is False and r["error_type"] == err


def test_unknown_tool_has_consistent_shape():
    r = tools.call_tool("cancel_service", {}, {})["result"]
    assert r["ok"] is False and r["error_type"] == "not_found"


def test_ticket_requires_verified_matching_customer():
    args = {"customer_id": "CUST-999", "category": "no_connection", "description": "x", "priority": "low"}
    r = tools.call_tool("create_support_ticket", args, {"verified_customer_id": "CUST-1"})["result"]
    assert r["error_type"] == "unauthorized" and not tools.MOCK_TICKET_STORE


def test_ticket_is_always_pending_and_only_a_human_function_approves():
    args = {"customer_id": "CUST-1", "category": "no_connection", "description": "x", "priority": "low"}
    r = tools.call_tool("create_support_ticket", args, {"verified_customer_id": "CUST-1"})["result"]
    assert r["output"]["status"] == "pending_approval"
    assert "approve_ticket" not in tools.TOOLS
    assert tools.approve_ticket(r["output"]["ticket_id"], "human")["status"] == "created"


@pytest.mark.parametrize("bad", [{"category": "billing_dispute"}, {"priority": "urgent"}, {"description": ""}])
def test_ticket_validation(bad):
    args = {"customer_id": "CUST-1", "category": "no_connection", "description": "x", "priority": "low", **bad}
    assert tools.call_tool("create_support_ticket", args, {"verified_customer_id": "CUST-1"})["result"]["error_type"] == "validation_error"
