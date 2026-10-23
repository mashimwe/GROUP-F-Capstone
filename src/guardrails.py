"""
ServiceFlow — Week 7 Guardrails
=================================
Input and output guardrails that sit AROUND the agent loop. They are
deliberately simple, deterministic and inspectable. Heuristic injection
detection cannot catch every paraphrase, so it is only one layer: the
architectural controls (tool allow-list, authorization, iteration limits and
the human-approval gate from Weeks 4-5) are what keep a missed injection
low-impact.
"""

import re
import unicodedata

MAX_INPUT_CHARS = 1000
MAX_OUTPUT_CHARS = 1500
# Everything before this marker is written by the system; everything after is quoted, human-approved guide text.
GUIDE_MARKER = "Here is guidance from our troubleshooting guide"


def system_authored_part(response: str) -> str:
    return response.split(GUIDE_MARKER, 1)[0]

# (regex, rule name) — applied to a normalised copy of the message
INJECTION_RULES = [
    (r"\b(ignore|disregard|forget)\b[^.]{0,25}\b(previous|prior|above|earlier|all)\b[^.]{0,25}\b(instructions?|rules?|prompts?)\b", "override_instructions"),
    (r"\b(ignore|disregard|forget)\b[^.]{0,15}\b(instructions?|rules?|prompts?|guidelines?)\b", "override_instructions"),
    (r"\b(reveal|show|print|tell me|repeat|leak)\b[^.]{0,25}\b(system )?(prompt|instructions)\b", "prompt_extraction"),
    (r"\bsystem prompt\b", "prompt_extraction"),
    (r"\byou are now\b", "role_override"),
    (r"\b(developer|admin|dan|jailbreak|god) mode\b", "role_override"),
    (r"\b(admin|administrator|root)\b[^.]{0,15}\b(password|credentials)\b", "credential_request"),
    (r"\b(call|invoke|execute|run)\b[^.]{0,40}\btool\b", "tool_invocation_attempt"),
    (r"(^|\n|\.\s)\s*(system|assistant)\s*:", "fake_role_marker"),
    (r"\b(other|all|every)\b[^.]{0,15}\bcustomers?\b[^.]{0,30}\b(tickets?|data|accounts?|records?)\b", "cross_customer_data"),
    (r"\b(all|every)\b[^.]{0,15}\btickets?\b", "cross_customer_data"),
    (r"\bapprove\b[^.]{0,20}\b(this|my|the|that)\b[^.]{0,10}\bticket\b", "approval_bypass_attempt"),
    (r"\b(ignore|disregard|forget|bypass|override)\b[^.]{0,25}\b(polic(y|ies)|restrictions?|safeguards?|programming)\b", "override_instructions"),
    (r"\b(what|which)\b[^.?]{0,30}\b(were you|have you been|you were)\b[^.?]{0,10}\b(given|told)\b", "prompt_extraction"),
    (r"\b(instructions|rules|prompt|guidelines)\b[^.?]{0,20}\b(you were|you've been|were you|have you been)\b[^.?]{0,10}\b(given|told)\b", "prompt_extraction"),
    (r"\brepeat\b[^.]{0,20}\b(word for word|verbatim)\b", "prompt_extraction"),
    (r"\bfrom now on\b[^.]{0,40}\b(act|behave|respond|answer|ignore|you (will|must|are|should))\b", "role_override"),
    (r"\bact as\b[^.]{0,30}\b(assistant|admin|developer|system|unrestricted)\b", "role_override"),
]

_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})

SAFE_MESSAGES = {
    "possible_prompt_injection": ("I can only help with internet service problems, and I can't act on instructions "
                                   "like that. If you describe your connection issue I'll gladly help, or I can "
                                   "pass you to a human agent."),
    "input_too_long": ("Your message is quite long. Could you summarise the problem in a few sentences "
                        "so I can help?"),
    "invalid_input": "I couldn't read that message. Could you describe your internet problem in a sentence or two?",
}

OUTPUT_FALLBACK = ("I'm not able to give a reliable answer to that automatically, so I'm passing this to a "
                    "human agent who can help you directly.")


def normalise_for_detection(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.translate(_LEET)
    return re.sub(r"\s+", " ", text)


def detect_injection(message: str) -> list:
    norm = normalise_for_detection(message)
    return sorted({name for pattern, name in INJECTION_RULES if re.search(pattern, norm)})


def validate_input(message) -> dict:
    """Returns {ok, cleaned, events, block_reason, safe_message}."""
    events = []
    if not isinstance(message, str):
        return {"ok": False, "cleaned": "", "block_reason": "invalid_input",
                "safe_message": SAFE_MESSAGES["invalid_input"],
                "events": [{"type": "input_blocked", "reason": "invalid_input"}]}

    cleaned = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", message).strip()
    if cleaned != message.strip():
        events.append({"type": "control_chars_stripped"})

    if len(cleaned) > MAX_INPUT_CHARS:
        events.append({"type": "input_blocked", "reason": "input_too_long", "length": len(cleaned)})
        return {"ok": False, "cleaned": cleaned, "block_reason": "input_too_long",
                "safe_message": SAFE_MESSAGES["input_too_long"], "events": events}

    rules = detect_injection(cleaned)
    if rules:
        events.append({"type": "injection_detected", "rules": rules})
        events.append({"type": "input_blocked", "reason": "possible_prompt_injection"})
        return {"ok": False, "cleaned": cleaned, "block_reason": "possible_prompt_injection",
                "safe_message": SAFE_MESSAGES["possible_prompt_injection"], "events": events}

    return {"ok": True, "cleaned": cleaned, "block_reason": None, "safe_message": None, "events": events}


OUTAGE_CLAIM = re.compile(r"(?<!whether )(?<!if )(?<!any )\bthere is an? (ongoing |confirmed |active )?outage\b|\bconfirmed outage\b", re.I)
FALSE_FINALITY = re.compile(r"\b(has been|have been|is now) (approved|created|resolved|refunded|cancel+ed)\b", re.I)
LEAK_TERMS = re.compile(r"system prompt|admin password|api[_ ]key", re.I)


def validate_output(response: str, state, context: dict) -> dict:
    """Checks the customer-facing text against the evidence the agent actually has."""
    violations = []
    out = state.outage_result if isinstance(state.outage_result, dict) else {}

    # Claim checks apply to what the SYSTEM asserts, not to quoted approved guide text, which may
    # legitimately contain negated or conditional wording such as "we will never say there is an outage unless...".
    if OUTAGE_CLAIM.search(system_authored_part(response)) and out.get("status") != "outage_confirmed":
        violations.append("unsupported_outage_claim")

    allowed_ids = {context.get("verified_customer_id")}
    if set(re.findall(r"CUST-\w+", response)) - allowed_ids:
        violations.append("other_customer_id_in_response")

    if LEAK_TERMS.search(response):
        violations.append("sensitive_term_in_response")

    if FALSE_FINALITY.search(response):
        violations.append("false_finality_claim")

    if state.stop_reason == "stop_resolved" and state.rag_attempted and "[Source:" not in response \
            and not (out.get("status") == "outage_confirmed" and not state.rag_attempted):
        violations.append("missing_source_citation")

    if len(response) > MAX_OUTPUT_CHARS:
        violations.append("response_too_long")

    return {"violations": violations, "fallback": OUTPUT_FALLBACK}
