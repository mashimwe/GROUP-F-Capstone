"""Verifies our model call matches the REAL google-genai SDK surface. No network: only the HTTP-level
method is stubbed, so classifier._call_gemini's own SDK usage code is what runs."""
import json

import pytest

genai_models = pytest.importorskip("google.genai.models")
import classifier  # noqa: E402


def test_real_sdk_call_shape(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "gemini")
    seen = {}

    class Resp:
        text = json.dumps({"category": "slow_connection", "confidence": "high"})

    def fake(self, *, model, contents, config=None):
        seen.update(model=model, contents=contents, config=config)
        return Resp()

    monkeypatch.setattr(genai_models.Models, "generate_content", fake)
    r = classifier.classify("my wifi is slow at night")
    assert r["category"] == "slow_connection" and r["source"] == f"gemini:{classifier.DEFAULT_MODEL}"
    assert seen["config"].temperature == 0 and seen["config"].response_mime_type == "application/json"
    assert "ServiceFlow" in seen["config"].system_instruction
    assert "my wifi is slow at night" in seen["contents"] and "CUSTOMER_MESSAGE" in seen["contents"]
