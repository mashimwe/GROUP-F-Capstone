# Prompts

| File | Purpose | Version |
|------|---------|---------|
| `classifier_system_v1.1.txt` | System prompt for the Gemini classifier slot (`src/classifier.py`) | v1.1 |

The customer message is sent as the *user* turn, wrapped in delimiters and labelled as data
(see `USER_TEMPLATE` in `src/classifier.py`). The model's output is never trusted: it is parsed,
validated against the six allowed categories, and any failure falls back to the keyword classifier.
Prompt changes must bump the version in the filename and be recorded in `CHANGELOG.md`.
