"""
ServiceFlow — Week 7 Service Pipeline
=======================================
The single entry point for one customer message:

  input guardrails -> agent loop (+ memory hint) -> response composer
  -> output guardrails -> structured trace

`guardrails_enabled=False` runs the same pipeline WITHOUT the guardrail layer
and WITHOUT the fail-safe exception handler. That is the "before" system used
for the pre-fix evaluation run, so before/after results are directly comparable.
"""

import time
import uuid

import agent
import guardrails
from agent_with_memory import run_agent_with_memory
from observability import fingerprint, steps_from_state
from case_session import CaseSession
from responder import compose_response

FAILSAFE_MESSAGE = "Something went wrong on our side, so I'm passing this to a human agent."


def components(guardrails_enabled: bool) -> dict:
    return {
        "classifier_mode": __import__("classifier").get_mode(),
        "classifier_model": __import__("classifier").get_model(),
        "classifier_prompt_version": "v1.1",
        "retriever": "TF-IDF cosine, k=3",
        "resolution_threshold": agent.RESOLUTION_THRESHOLD,
        "max_iterations": agent.MAX_ITERATIONS,
        "max_tool_retries": agent.MAX_TOOL_RETRIES,
        "guardrails_enabled": guardrails_enabled,
    }


def handle_customer_message(message, context, store, tracer=None, guardrails_enabled=True, scenario_id=None, session=None):
    run_id = uuid.uuid4().hex[:12]
    t0 = time.perf_counter()
    events, error, state, duplicate = [], None, None, None
    stop_reason, response = None, None
    original = message

    try:
        if guardrails_enabled:
            gv = guardrails.validate_input(message)
            events += gv["events"]
            if not gv["ok"]:
                stop_reason, response = "blocked_by_guardrail", gv["safe_message"]
            else:
                message = gv["cleaned"]

        continued = False
        if session is not None:
            session.bind(context.get("verified_customer_id"))
            effective = session.effective_message(message)
            continued = effective != message
            if continued and guardrails_enabled:
                # the combined text is re-checked: an injection could be split across two turns
                gv2 = guardrails.validate_input(effective)
                events += [e for e in gv2["events"] if e["type"] != "control_chars_stripped"]
                if not gv2["ok"]:
                    stop_reason, response = "blocked_by_guardrail", gv2["safe_message"]
            message_for_agent = effective
        else:
            message_for_agent = message

        if response is None:
            agent_context = dict(context)
            if session is not None:
                agent_context["clarification_rounds"] = session.rounds
            if continued:
                agent_context["latest_message"] = message
            state, duplicate = run_agent_with_memory(message_for_agent, agent_context, store)
            stop_reason = state.stop_reason
            response = compose_response(state)
            if guardrails_enabled:
                ov = guardrails.validate_output(response, state, context)
                if ov["violations"]:
                    events.append({"type": "output_blocked", "violations": ov["violations"]})
                    response = ov["fallback"]
    except Exception as exc:  # noqa: BLE001
        error = repr(exc)
        if not guardrails_enabled:
            _trace(tracer, run_id, scenario_id, original, context, events, state, duplicate, stop_reason, response, error, t0, guardrails_enabled)
            raise
        events.append({"type": "failsafe_triggered", "error": error})
        stop_reason, response = "error_failsafe", FAILSAFE_MESSAGE

    if session is not None and state is not None:
        session.update(message, stop_reason)  # only successfully processed turns enter the session
    record = _trace(tracer, run_id, scenario_id, original, context, events, state, duplicate, stop_reason, response, error, t0, guardrails_enabled)
    return {"run_id": run_id, "stop_reason": stop_reason, "response": response, "state": state,
            "duplicate": duplicate, "events": events, "latency_ms": record["latency_ms"], "error": error}


def _trace(tracer, run_id, scenario_id, original, context, events, state, duplicate, stop_reason, response, error, t0, gr):
    steps, retrieval, tools = steps_from_state(state)
    record = {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "input": {"sha256_12": fingerprint(original), "length": len(original) if isinstance(original, str) else None},
        "authenticated": bool(context.get("verified_customer_id")),
        "components": components(gr),
        "guardrail_events": events,
        "category": state.category if state else None,
        "classifier_source": next((st["detail"].get("source") for st in (state.trace if state else []) if st["action"] == "classify"), None),
        "steps": steps,
        "retrieval": retrieval,
        "tool_calls": tools,
        "duplicate_hint": bool(duplicate),
        "outcome": stop_reason,
        "ticket_id": state.ticket_id if state else None,
        "response_preview": (response or "")[:160],
        "error": error,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
    }
    if tracer:
        tracer.write(record)
    return record
