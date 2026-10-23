# ServiceFlow — an AI-assisted internet help-desk triage agent

**BSE4104 AI-Native & Agentic Engineering Capstone · Group F · Release v1.0.0**

ServiceFlow helps customers of an internet service provider with connection problems. It classifies the
problem, checks outage status through an approved tool, answers from a controlled troubleshooting knowledge
base **with a cited source**, and, when it cannot answer confidently, prepares a support ticket that **a human
must approve**. It is deliberately *bounded*: it cannot change infrastructure, approve its own tickets, or act
outside a fixed list of tools. All data in this repository is synthetic.

## How it works

```
customer message
   -> input guardrails (length, control chars, prompt-injection rules)
   -> classifier (Gemini, validated; keyword fallback)            src/classifier.py
   -> bounded agent loop (max 6 steps, allow-listed actions)      src/agent.py
        |-- check_outage_status  (read-only tool)                 src/tools.py
        |-- retrieve guides (TF-IDF, category-gated, cited)       src/rag_pipeline.py
        `-- create_support_ticket -> PENDING_APPROVAL (human approves)
   -> response composer (deterministic, cites sources)            src/responder.py
   -> output guardrails -> structured trace (no raw message text) src/observability.py
```
Session state (`src/case_session.py`, one open case) and persistent memory (`src/memory_store.py`, minimal
case history for duplicate-ticket hints) are separate objects with separate lifetimes.

## Quick start (about 3 minutes, no API key needed)

```bash
git clone https://github.com/mashimwe/GROUP-F-Capstone.git && cd GROUP-F-Capstone
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest                                           # 79 tests, offline
SERVICEFLOW_CLASSIFIER=keyword python src/run_demo.py      # scripted 7-scene demo (Windows: set the variable first)
SERVICEFLOW_CLASSIFIER=keyword python src/run_demo.py --interactive
```

## Using the Gemini model (optional, needs your own key)

```bash
export GEMINI_API_KEY=your-key          # never commit it; see .env.example
python src/run_demo.py                  # auto mode: uses Gemini when a key is set
python src/gemini_eval.py               # Gemini vs keyword accuracy -> evidence/evaluation/classifier_comparison.*
python src/eval_harness.py gemini_dev on --set dev --classifier gemini --out evidence/evaluation
```
The model is treated as untrusted: its reply must be valid JSON with an allowed category, low confidence is
treated as "unclear", and any error/timeout falls back to keyword rules (logged in the trace). Default model
`gemini-3.5-flash-lite`; override with `GEMINI_MODEL`. (`gemini-2.0-flash` was shut down on 2026-06-01.)
Free-tier requests may be used by Google to improve its products, so **send only synthetic text**.

## Reproduce the evaluation

| Command | What it does |
|---|---|
| `python src/eval_harness.py dev on --set dev --out evidence/evaluation` | 46 development scenarios (normal, edge, incorrect info, adversarial, tool failure, unauthorized) |
| `python src/eval_harness.py held on --set heldout --out evidence/evaluation` | 20 held-out scenarios written before the first run |
| `python src/guardrail_tests.py` | 19 targeted guardrail tests |
| `python src/eval_harness.py base off --set dev --out /tmp/x` | same set with guardrails off (the "before" system) |

## Results (offline keyword classifier, reproducible)

| Evaluation | Result |
|---|---|
| Unit/integration tests (pytest) | 79 pass |
| Development set (46) | **44/46 (95.7%)**, 0 safety violations, 0 crashes (was 25/46 before Week 7 fixes) |
| Held-out set (20), first run, frozen | **11/20 (55%)** |
| Held-out set after fixes (3 scenarios drove fixes) | 14/20 (70%); all 6 remaining failures are keyword-classifier vocabulary |
| Keyword classifier on 27 labelled messages | 20/27 (74.1%) |
| Gemini classifier on the same 27 | **not measured by the author of this release; run `python src/gemini_eval.py`** |

The development-set score is optimistic because fixes were developed against it. The held-out figure is the
honest generalisation estimate for the offline fallback.

## Repository layout

```
src/         application code, evaluation harness, demo        tests/      pytest suite (79 tests)
prompts/     versioned classifier prompt (v1.1)                 knowledge/  15 guides + SOURCE_REGISTER.csv
docs/        requirements, architecture, weekly reports, final report
evidence/    evaluation results, traces (JSONL), demo transcript, screenshots/
.github/workflows/ci.yml   runs the tests and the dev evaluation on every push
```

## Safety design (what holds even if one layer fails)

Tool allow-list enforced in the loop · iteration limit 6 · one retry, only for transient errors ·
authorization checked before any ticket tool runs · tickets are created `pending_approval` and **no tool can
approve one** · anonymous sessions never read/write memory · traces store a message fingerprint, not the text.

## Known limitations (see docs/final-report for detail)

1. **Keyword fallback is brittle** on natural phrasing (e.g. "out", "disconnects"): it fails safely (asks a question) but often.
2. **"No wifi."** is answered with the router factory-reset guide: lexical retrieval matches words, not meaning (FC-10, open).
3. **Paraphrased prompt injection** with no trigger words is not caught by the pattern rules (FC-11, open); other layers contain the impact.
4. Answers are composed from guide text, not generated; clarification questions are fixed templates (a safety choice that deviates from the Week 1 boundary matrix).
5. Outage and ticket systems are simulated. Latency figures exclude any model call.
6. Retrieval resolution margin is small (threshold 0.15; some correct answers score ~0.15-0.18).

## Releasing

```bash
git add -A && git commit -m "Release v1.0.0"
git tag -a v1.0.0 -m "ServiceFlow v1.0.0 - capstone final release"
git push origin main --tags
```

## AI assistance

AI assistants were used throughout design, coding, documentation and review. See `docs/final-report`
(AI Engineering Log appendix). Team members are accountable for everything submitted and must be able to
explain and run it.

Authors: Buyinza Samuel · Bahati Brenda Kizito · Aruho Priscillah · Andimashimwe Rhoda · Nuwahereza Dennise
