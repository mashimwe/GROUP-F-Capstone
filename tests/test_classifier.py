import json
import time

import pytest

import classifier


def test_keyword_basic():
    assert classifier.keyword_classify("My router light is blinking")["category"] == "router_modem_issue"
    assert classifier.keyword_classify("asdkjaskjd")["category"] == "unclear"


@pytest.mark.parametrize("raw,category", [
    ('{"category": "slow_connection", "confidence": "high"}', "slow_connection"),
    ('```json\n{"category": "no_connection", "confidence": "medium"}\n```', "no_connection"),
    ('{"category": "no_connection", "confidence": "low"}', "unclear"),            # low confidence is not acted on
    ('{"category": "no_connection", "confidence": "banana"}', "unclear"),          # bad confidence -> low -> unclear
])
def test_parse_accepts_and_downgrades(raw, category):
    assert classifier.parse_model_output(raw)["category"] == category


@pytest.mark.parametrize("raw", ["", None, "not json", "[]", '{"category": "refund_everything", "confidence": "high"}', '{"confidence": "high"}'])
def test_parse_rejects_untrusted_output(raw):
    with pytest.raises(ValueError):
        classifier.parse_model_output(raw)


def test_gemini_success_is_labelled(monkeypatch):
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(classifier, "_call_gemini", lambda m: json.dumps({"category": "slow_connection", "confidence": "high"}))
    r = classifier.classify("anything")
    assert r["category"] == "slow_connection" and r["source"].startswith("gemini:")


@pytest.mark.parametrize("bad_call", [
    lambda m: "garbage",
    lambda m: '{"category": "delete_all_tickets", "confidence": "high"}',
    lambda m: (_ for _ in ()).throw(RuntimeError("api down")),
])
def test_any_model_failure_falls_back_to_keyword(monkeypatch, bad_call):
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(classifier, "_call_gemini", bad_call)
    r = classifier.classify("my router is blinking")
    assert r["category"] == "router_modem_issue" and r["source"] == "keyword" and r["fallback_reason"]


def test_timeout_falls_back(monkeypatch):
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_TIMEOUT_S", "0.05")
    monkeypatch.setattr(classifier, "_call_gemini", lambda m: time.sleep(0.5) or "{}")
    r = classifier.classify("slow internet")
    assert r["source"] == "keyword" and "Timeout" in r["fallback_reason"]


def test_gemini_mode_without_key_degrades_safely(monkeypatch):
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "gemini")
    r = classifier.classify("slow internet")
    assert r["source"] == "keyword" and r["fallback_reason"] == "no_api_key"


def test_auto_mode_uses_model_only_when_key_present(monkeypatch):
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "auto")
    assert classifier.classify("slow internet")["source"] == "keyword"
    classifier.clear_cache()
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr(classifier, "_call_gemini", lambda m: '{"category": "slow_connection", "confidence": "high"}')
    assert classifier.classify("slow internet")["source"].startswith("gemini:")


def test_prompt_is_versioned_and_loadable():
    assert "ServiceFlow" in classifier.load_prompt()


def test_model_is_not_the_shut_down_one():
    assert not classifier.DEFAULT_MODEL.startswith("gemini-2.0")
