# Evidence pack index

| Path | What it is | How to reproduce |
|---|---|---|
| `evaluation/results_run_dev_final.json` | 46 development scenarios, final release | `python src/eval_harness.py dev_final on --set dev --out evidence/evaluation` |
| `evaluation/results_run_heldout_frozen.json` | 20 held-out scenarios, **first run, frozen** (knowledge base v1.0, before any fix) | cannot be reproduced exactly: code and guides have changed since; kept as the honest first result |
| `evaluation/results_run_heldout_after_fixes.json` | same 20 after fixes (H15, H16, H20 drove fixes, so no longer held-out) | `python src/eval_harness.py heldout_after_fixes on --set heldout --out evidence/evaluation` |
| `evaluation/traces_run_*.jsonl` | one structured trace per message for each run (no raw customer text) | produced by the same commands |
| `evaluation/week7/` | Week 7 baseline: the Week 6 system before fixes (25/46) and the Week 7 final | historical record |
| `evaluation/guardrail_tests.json` | 19 targeted guardrail tests | `python src/guardrail_tests.py` |
| `evaluation/classifier_comparison.*` | keyword baseline on 27 labelled messages (20/27). **Gemini column empty until you run it** | `python src/gemini_eval.py` (needs `GEMINI_API_KEY`) |
| `demo/demo_transcript.txt` | scripted 7-scene demo with trace views | `python src/run_demo.py` |
| `traces/` | copies of the main trace files | |
| `screenshots/` | **to be captured by the team** (see its README) | |

Test suite: `python -m pytest` (79 tests, includes two regression gates over the dev and held-out sets).
CSV versions of the datasets and results are in `docs/evaluation/`.
