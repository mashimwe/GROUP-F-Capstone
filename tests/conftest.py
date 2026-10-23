import os
import sys

import pytest

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(SRC))
os.environ["SERVICEFLOW_CLASSIFIER"] = "keyword"   # offline, reproducible
os.environ.pop("GEMINI_API_KEY", None)


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    import classifier
    import tools
    monkeypatch.setenv("SERVICEFLOW_CLASSIFIER", "keyword")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    classifier.clear_cache()
    tools.MOCK_TICKET_STORE.clear()
    yield
    classifier.clear_cache()
    tools.MOCK_TICKET_STORE.clear()
