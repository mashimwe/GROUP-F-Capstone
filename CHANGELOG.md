# Changelog

## v1.0.0 — Week 8 final release
**Added**
- `classifier.py`: Gemini model integration (validated output, timeout, safe keyword fallback, trace of which classifier answered). Default model `gemini-3.5-flash-lite`.
- `case_session.py`: clarification replies now continue the open case (User Stories 5 and 8); session text is discarded when the case closes.
- Tickets now carry the report, category, outage/retrieval evidence and a human-follow-up flag (User Story 7).
- 20 held-out evaluation scenarios, `gemini_eval.py`, 27 labelled classifier cases.
- `pytest` suite (79 tests, including mutation-checked guardrails and a real-SDK contract test), CI workflow, `run_demo.py`, README, `.env.example`.
**Fixed**
- Week 2 baseline used `gemini-2.0-flash`, which Google shut down on 2026-06-01. Model is now configurable.
- Injection rules missed "ignore company policy" and "what instructions were you given" (held-out H15, H16).
- Retrieval was diluted when a clarification reply was joined to the first message (held-out H20); newest message is now tried first.
- Output guardrail wrongly blocked approved guide text containing negated outage wording; claim checks now apply only to system-authored text.
- Six knowledge-base guides were written for staff but shown to customers; rewritten in customer voice (knowledge base v1.1).
**Removed**
- Unused, never-evaluated generative-answer function in `rag_pipeline.py` (answers are composed deterministically).
**Known open**: FC-10 ("No wifi." retrieval), FC-11 (paraphrased injection), keyword-classifier vocabulary gaps.

## v0.7 — Week 7: evaluation, tracing, guardrails (46 scenarios; 25/46 -> 44/46)
## v0.6 — Week 6: session/persistent memory separation, duplicate-ticket hint, MCP-style interface spec
## v0.5 — Week 5: bounded agent loop, task contract, execution traces
## v0.4 — Week 4: tools, authorization, human-approval gate
## v0.3 — Week 3: controlled corpus, TF-IDF retrieval, 15-case RAG evaluation
## v0.2 — Week 2: model selection, prompt specification
## v0.1 — Week 1: charter, user stories, AI boundary matrix
