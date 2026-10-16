"""
ServiceFlow — Week 7 Response Composer
========================================
Turns the final AgentState into the text a customer would actually see.
Deterministic and template-based on purpose: every factual claim comes from
a tool result or a retrieved document, and every RAG-based answer carries a
[Source: <doc id>] citation so groundedness can be checked mechanically.
"""


def _top_hit(state):
    for step in reversed(state.trace):
        if step["action"] == "retrieve_and_answer":
            hits = step["detail"].get("hits", [])
            return hits[0] if hits else None
    return None


def _outage_prefix(state):
    out = state.outage_result
    if not out:
        return ""
    status = out.get("status") if isinstance(out, dict) else None
    if status == "no_known_outage":
        return "No outage is currently reported for your area. "
    if status == "area_not_found":
        return ("I couldn't find that service area in our status system, so I can't "
                "confirm whether there is an outage. ")
    if status == "outage_confirmed":
        return ""
    return "I couldn't check outage status right now, so I can't confirm whether there is an outage. "


def compose_response(state) -> str:
    reason = state.stop_reason
    prefix = _outage_prefix(state)
    out = state.outage_result if isinstance(state.outage_result, dict) else {}

    if reason == "stop_resolved":
        if out.get("status") == "outage_confirmed" and not state.rag_attempted:
            eta = out.get("eta_minutes")
            eta_text = f" Estimated restoration: about {eta} minutes." if eta else ""
            return (f"There is a confirmed outage affecting your area (incident {out.get('incident_id')}).{eta_text} "
                    "No action is needed from you.")
        hit = _top_hit(state)
        if hit:
            return (f"{prefix}Here is guidance from our troubleshooting guide "
                    f"\"{hit['title']}\" [Source: {hit['id']}]: {hit['chunk_text']}")
        return prefix + "I found guidance for this but couldn't display it; a human agent will follow up."

    if reason == "stop_waiting_for_customer":
        return (prefix + "Could you tell me more about what's happening with your connection? "
                "For example: no connection, slow speeds, or the connection dropping.")

    if reason == "stop_handoff_pending_approval":
        return (f"{prefix}I couldn't find a confident answer in our guides, so I've prepared support ticket "
                f"{state.ticket_id} for our team to review. It is pending approval and has not been actioned yet.")

    if reason == "stop_requires_verification":
        return ("To open a support ticket I need to verify your account first. "
                "Please sign in or contact our support line.")

    if reason == "stop_escalated_human":
        return prefix + "I couldn't complete that automatically, so I'm passing this to a human agent."

    if reason == "max_iterations_reached":
        return prefix + "I wasn't able to finish this automatically, so I'm handing it to a human agent."

    return "I'm passing this to a human agent so they can help you directly."
