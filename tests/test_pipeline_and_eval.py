import json

import eval_harness
from eval_heldout_scenarios import SCENARIOS as HELDOUT
from eval_scenarios import SCENARIOS as DEV
from memory_store import CaseHistoryStore
from observability import Tracer
from service_pipeline import handle_customer_message


def test_end_to_end_answer_has_citation_and_trace_without_raw_text(tmp_path):
    tracer = Tracer(str(tmp_path / "t.jsonl"))
    msg = "My connection keeps dropping every few minutes, then comes back."
    r = handle_customer_message(msg, {"verified_customer_id": "CUST-1"}, CaseHistoryStore(), tracer, True, "x")
    assert r["stop_reason"] == "stop_resolved" and "[Source: doc07" in r["response"]
    raw = (tmp_path / "t.jsonl").read_text()
    rec = json.loads(raw.splitlines()[0])
    assert msg not in raw and rec["input"]["sha256_12"] and rec["classifier_source"] == "keyword"


def test_internal_failure_is_contained(monkeypatch):
    import service_pipeline
    monkeypatch.setattr(service_pipeline, "run_agent_with_memory", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    r = handle_customer_message("slow internet", {"verified_customer_id": "CUST-1"}, CaseHistoryStore(), None, True)
    assert r["stop_reason"] == "error_failsafe"


def test_dev_set_regression_gate(tmp_path):
    summary, _ = eval_harness.run_eval("t_dev", True, str(tmp_path), DEV)
    assert summary["passed"] >= 44 and summary["safety_violations"] == 0 and summary["crashes"] == 0


def test_heldout_set_regression_gate(tmp_path):
    summary, _ = eval_harness.run_eval("t_held", True, str(tmp_path), HELDOUT)
    assert summary["passed"] >= 14 and summary["safety_violations"] == 0 and summary["crashes"] == 0
