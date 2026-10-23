"""
ServiceFlow — Week 3 RAG Pipeline
==================================
Adds a controlled, traceable knowledge source on top of the Week 2
classification baseline. This script implements ingestion, chunking,
indexing and retrieval end-to-end and runs entirely offline (no API key
needed) — you can run this yourself right now to reproduce every result
in the 15-case evaluation table. Customer-facing text is composed deterministically from the retrieved
chunk by responder.py (no generative step), so every answer is traceable to a source document.

Pipeline stages
---------------
1. Ingestion   : read every .md file in knowledge/
2. Chunking    : one chunk per document (see design note below)
3. Indexing    : TF-IDF vectorisation of all chunks
4. Retrieval   : cosine similarity, top-k chunks per query
5. Grounding   : assemble retrieved chunks + source citations into context

Chunking design note
---------------------
Each source document already covers exactly one troubleshooting scenario
in 60-120 words, so document-level chunking (one chunk = one document) was
chosen over paragraph/sentence splitting. Splitting further would separate
a symptom from its cause and lose meaning; the corpus was deliberately
written at "one chunk" granularity instead.
"""

import glob
import json
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_HERE = os.path.dirname(os.path.abspath(__file__))
# Works with knowledge/ next to this file, or one level up (src/ + top-level knowledge/ repo layout).
KNOWLEDGE_DIR = next((p for p in (os.path.join(_HERE, "knowledge"), os.path.join(_HERE, "..", "knowledge"))
                      if os.path.isdir(p)), os.path.join(_HERE, "knowledge"))


# ---------------------------------------------------------------------------
# 1. Ingestion + 2. Chunking
# ---------------------------------------------------------------------------
def load_corpus():
    """Read every knowledge/*.md file and parse its front-matter + body."""
    docs = []
    for path in sorted(glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        title_m = re.search(r"^Title:\s*(.+)$", text, re.MULTILINE)
        category_m = re.search(r"^Category:\s*(.+)$", text, re.MULTILINE)
        source_m = re.search(r"^Source:\s*(.+)$", text, re.MULTILINE)
        body = re.split(r"^Source:.*$", text, flags=re.MULTILINE)[-1].strip()
        docs.append({
            "id": os.path.basename(path).replace(".md", ""),
            "title": title_m.group(1).strip() if title_m else "",
            "category": category_m.group(1).strip() if category_m else "",
            "source": source_m.group(1).strip() if source_m else "",
            "chunk_text": body,
        })
    return docs


# ---------------------------------------------------------------------------
# 3. Indexing
# ---------------------------------------------------------------------------
class RagIndex:
    def __init__(self, docs):
        self.docs = docs
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = self.vectorizer.fit_transform([d["chunk_text"] for d in docs])

    # -----------------------------------------------------------------
    # 4. Retrieval
    # -----------------------------------------------------------------
    def retrieve(self, query, k=3, min_score=0.08):
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix)[0]
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:k]:
            if scores[i] >= min_score:
                results.append({**self.docs[i], "score": round(float(scores[i]), 3)})
        return results


# ---------------------------------------------------------------------------
# 5. Grounding — build the context block and detect the unanswerable case
# ---------------------------------------------------------------------------
def build_context(retrieved):
    if not retrieved:
        return None  # signals "no supporting evidence found"
    lines = []
    for r in retrieved:
        lines.append(f"[Source: {r['id']} — {r['title']}]\n{r['chunk_text']}")
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# 15-case RAG evaluation set (answerable / partially answerable / unanswerable)
# ---------------------------------------------------------------------------
RAG_TEST_QUESTIONS = [
    {"id": 1, "type": "answerable", "question": "My internet is completely down, what should I try first?"},
    {"id": 2, "type": "answerable", "question": "What do the lights on my router mean?"},
    {"id": 3, "type": "answerable", "question": "My internet is slow every evening when everyone is home."},
    {"id": 4, "type": "answerable", "question": "My connection keeps dropping for a few seconds and then comes back."},
    {"id": 5, "type": "answerable", "question": "How do I change my Wi-Fi password?"},
    {"id": 6, "type": "answerable", "question": "How do I run an accurate speed test?"},
    {"id": 7, "type": "answerable", "question": "My router feels very hot and keeps disconnecting."},
    {"id": 8, "type": "partially_answerable", "question": "My connection is slow and drops every few minutes, and will I get a refund for the downtime?"},
    {"id": 9, "type": "partially_answerable", "question": "Is there an outage in my area, and if so when will it be fixed and can I get compensation?"},
    {"id": 10, "type": "partially_answerable", "question": "My router is 6 years old, keeps losing its settings, and I also want to know if I should upgrade to fibre."},
    {"id": 11, "type": "partially_answerable", "question": "Wi-Fi is slow in my bedroom but fine near the router — should I just buy a new router entirely?"},
    {"id": 12, "type": "unanswerable", "question": "How much does a new fibre installation cost at a different address?"},
    {"id": 13, "type": "unanswerable", "question": "Can I get a static IP address for my home connection?"},
    {"id": 14, "type": "unanswerable", "question": "What is your policy on refunds for repeated outages?"},
    {"id": 15, "type": "unanswerable", "question": "Is my personal data shared with third parties?"},
]


if __name__ == "__main__":
    docs = load_corpus()
    index = RagIndex(docs)
    print(f"Loaded {len(docs)} documents into the index.\n")

    for case in RAG_TEST_QUESTIONS:
        results = index.retrieve(case["question"], k=3)
        print(f"--- Case {case['id']} [{case['type']}] ---")
        print(f"Q: {case['question']}")
        if results:
            for r in results:
                print(f"   retrieved: {r['id']} ({r['title']}) score={r['score']}")
        else:
            print("   retrieved: NONE (below similarity threshold)")
        print()
