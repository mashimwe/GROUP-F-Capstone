"""
Measure the Gemini classifier against the offline keyword fallback on labelled cases.

    export GEMINI_API_KEY=...            (never commit it)
    python gemini_eval.py                -> evidence/evaluation/classifier_comparison.{json,csv}

Without a key the keyword column is still produced and the Gemini column is skipped.
Only synthetic cases are sent to the model (free-tier content may be used by Google to improve products).
"""
import csv
import json
import os
import time
from datetime import datetime, timezone

import classifier
from eval_classifier_cases import CASES


def main(out_dir="evidence/evaluation"):
    os.makedirs(out_dir, exist_ok=True)
    have_key = bool(os.environ.get("GEMINI_API_KEY"))
    rows, kw_ok, gm_ok, gm_errors, lat = [], 0, 0, 0, []
    for message, gold in CASES:
        kw = classifier.keyword_classify(message)["category"]
        kw_ok += kw == gold
        gm, gm_err, ms = None, None, None
        if have_key:
            t0 = time.perf_counter()
            try:
                gm = classifier.classify_with_gemini(message)["category"]
            except Exception as exc:  # noqa: BLE001
                gm_err = f"{type(exc).__name__}: {str(exc)[:100]}"
                gm_errors += 1
            ms = round((time.perf_counter() - t0) * 1000, 1)
            lat.append(ms)
            gm_ok += gm == gold
        rows.append({"message": message, "gold": gold, "keyword": kw, "keyword_correct": kw == gold,
                     "gemini": gm, "gemini_correct": (gm == gold) if gm else None, "gemini_error": gm_err, "gemini_ms": ms})
    n = len(CASES)
    summary = {"run_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cases": n,
               "keyword_accuracy": f"{kw_ok}/{n} ({100 * kw_ok / n:.1f}%)",
               "model": classifier.get_model() if have_key else None,
               "gemini_accuracy": f"{gm_ok}/{n} ({100 * gm_ok / n:.1f}%)" if have_key else "skipped (no GEMINI_API_KEY)",
               "gemini_errors": gm_errors if have_key else None,
               "gemini_latency_ms_median": sorted(lat)[len(lat) // 2] if lat else None,
               "gemini_latency_ms_max": max(lat) if lat else None}
    with open(os.path.join(out_dir, "classifier_comparison.json"), "w") as f:
        json.dump({"summary": summary, "rows": rows}, f, indent=1)
    with open(os.path.join(out_dir, "classifier_comparison.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(json.dumps(summary, indent=1))
    for r in rows:
        if not r["keyword_correct"] or r["gemini_correct"] is False or r["gemini_error"]:
            print(f"  gold={r['gold']:24} keyword={r['keyword']:24} gemini={r['gemini']} {r['gemini_error'] or ''} | {r['message'][:60]}")


if __name__ == "__main__":
    main()
