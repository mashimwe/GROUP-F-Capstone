"""
ServiceFlow — Week 7 Observability
====================================
One structured JSON record per customer message, appended to a .jsonl file.
Captures component/prompt versions, guardrail events, every agent step with
timing, retrieval hits (doc id + score), tool calls (ok / error type), total
latency and the final outcome.

Privacy decision (consistent with Week 6): the raw customer message is NOT
logged. Only its length and a short SHA-256 fingerprint are kept, so a run
can be matched to a known input without retaining the text.
"""

import hashlib
import json
import os
import statistics

TOOL_STEPS = {"check_outage_status", "check_outage_status_failed", "create_support_ticket"}


def fingerprint(text) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:12]


def steps_from_state(state):
    steps, retrieval, tools = [], [], []
    if state is None:
        return steps, retrieval, tools
    for s in state.trace:
        steps.append({"iteration": s["iteration"], "action": s["action"], "t_ms": s.get("t_ms")})
        d = s["detail"] if isinstance(s["detail"], dict) else {}
        if s["action"] == "retrieve_and_answer":
            retrieval = [{"doc_id": h["id"], "score": h["score"]} for h in d.get("hits", [])]
            retrieval_resolved = d.get("resolved")
            steps[-1]["resolved"] = retrieval_resolved
        if s["action"] in TOOL_STEPS:
            tools.append({"tool": s["action"].replace("_failed", ""), "ok": bool(d.get("ok", s["action"] != "check_outage_status_failed")),
                          "error_type": d.get("error_type"), "t_ms": s.get("t_ms")})
    return steps, retrieval, tools


class Tracer:
    def __init__(self, path=None):
        self.path = path
        self.records = []
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "w").close()

    def write(self, record: dict):
        self.records.append(record)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")

    def latency_summary(self):
        vals = sorted(r["latency_ms"] for r in self.records if "latency_ms" in r)
        if not vals:
            return {}
        p95 = vals[min(len(vals) - 1, int(round(0.95 * (len(vals) - 1))))]
        return {"n": len(vals), "p50_ms": round(statistics.median(vals), 2), "p95_ms": round(p95, 2), "max_ms": round(vals[-1], 2)}
