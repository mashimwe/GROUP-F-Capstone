import agent
import tools

CTX = {"verified_customer_id": "CUST-1"}
NICHE = ("My smart TV app drops out for exactly one second every night at midnight, nothing else does this, "
         "already tried the standard fixes, please escalate")


def test_resolved_by_retrieval():
    st = agent.run_agent("My connection keeps dropping every few minutes, then comes back.", dict(CTX))
    assert st.stop_reason == "stop_resolved" and st.rag_answer["top_source"].startswith("doc07")


def test_outage_confirmed_stops_without_retrieval():
    st = agent.run_agent("Is there an outage in my area?", {**CTX, "area_code": "KLA-05"})
    assert st.stop_reason == "stop_resolved" and not st.rag_attempted


def test_unresolved_creates_pending_ticket_with_evidence():
    st = agent.run_agent(NICHE, dict(CTX))
    t = tools.MOCK_TICKET_STORE[-1]
    assert st.stop_reason == "stop_handoff_pending_approval" and t.status == "pending_approval"
    for needle in ("Customer report:", "System category: intermittent_connection", "no guide matched", "HUMAN FOLLOW-UP REQUIRED"):
        assert needle in t.description


def test_unauthenticated_ticket_is_refused_without_retry_loop():
    st = agent.run_agent(NICHE, {})
    assert st.stop_reason == "stop_requires_verification" and not tools.MOCK_TICKET_STORE
    assert sum(s["action"] == "create_support_ticket" for s in st.trace) == 0


def test_validation_error_is_not_retried():
    st = agent.run_agent("Is there an outage in my area?", {**CTX, "area_code": "kla5"})
    assert sum(s["action"].startswith("check_outage_status") for s in st.trace) == 1


def test_unavailable_tool_retried_once_then_falls_back():
    st = agent.run_agent("Is there an outage? My connection just went completely dead.", {**CTX, "area_code": "DWN-99"})
    assert sum(s["action"].startswith("check_outage_status") for s in st.trace) == 2 and st.stop_reason == "stop_resolved"


def test_malformed_tool_response_does_not_crash(monkeypatch):
    monkeypatch.setitem(tools.TOOLS, "check_outage_status", lambda a, c: "OK")
    st = agent.run_agent("Is there an outage in my area?", {**CTX, "area_code": "KLA-05"})
    assert st.stop_reason == "stop_resolved" and st.outage_result["status"] == "check_failed"


def test_iteration_limit(monkeypatch):
    monkeypatch.setattr(agent, "plan_next_action", lambda s: "classify")
    st = agent.run_agent("x", dict(CTX))
    assert st.stop_reason == "max_iterations_reached" and st.iteration == agent.MAX_ITERATIONS


def test_unapproved_action_is_refused(monkeypatch):
    monkeypatch.setattr(agent, "plan_next_action", lambda s: "cancel_service")
    st = agent.run_agent("x", dict(CTX))
    assert st.stop_reason == "stop_escalated_human" and not tools.MOCK_TICKET_STORE


def test_faq_question_is_answered_not_clarified():
    st = agent.run_agent("How do I change my Wi-Fi password?", dict(CTX))
    assert st.stop_reason == "stop_resolved" and st.rag_answer["top_source"].startswith("doc15")


def test_out_of_scope_question_is_not_answered_from_an_unrelated_guide():
    st = agent.run_agent("How much does a new fibre installation cost at a different address?", dict(CTX))
    assert st.stop_reason != "stop_resolved"
