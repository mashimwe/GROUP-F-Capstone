"""
ServiceFlow — Week 2 baseline, updated for the release.

Classifies one message with the configured model and prints the validated result.
    python serviceflow_baseline.py "My internet keeps dropping every few minutes"

Needs GEMINI_API_KEY (see .env.example). Without it, the keyword fallback answers and
says so. NOTE: the Week 2 version of this file used `gemini-2.0-flash`, which Google shut
down on 1 June 2026. The model is now configurable (GEMINI_MODEL, default in classifier.py).
"""
import json
import os
import sys

os.environ.setdefault("SERVICEFLOW_CLASSIFIER", "gemini")
import classifier  # noqa: E402

if __name__ == "__main__":
    message = " ".join(sys.argv[1:]) or "My connection keeps dropping every few minutes, then comes back."
    print(json.dumps({"input": message, "result": classifier.classify(message)}, indent=2))
