"""Tiny keyword-overlap RAG over kb.md (swap for embeddings + a vector DB in production)."""
import re
from pathlib import Path

def _chunks():
    out = []
    kb_path = Path(__file__).with_name("kb.md")
    for block in kb_path.read_text(encoding="utf-8").split("## ")[1:]:
        head, body = block.split("\n", 1)
        cid, src = [x.strip() for x in head.split("|")]
        out.append({"id": cid, "source": src, "text": body.strip()})
    return out

def search(query: str, k: int = 1):
    q = set(re.findall(r"\w+", query.lower()))
    words = lambda c: set(re.findall(r"\w+", (c["id"] + " " + c["text"]).lower()))
    return sorted(_chunks(), key=lambda c: -len(q & words(c)))[:k]
