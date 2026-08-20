"""
A small, dependency-free recursive-ish text splitter. Splits on paragraph
breaks first, falls back to sentence breaks for long paragraphs, and
hard-slices anything still too long. Keeps a character overlap between
consecutive chunks so context isn't lost at chunk boundaries.
"""

import re
from typing import List

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


def _split_sentences(paragraph: str) -> List[str]:
    return [s for s in _SENTENCE_SPLIT.split(paragraph) if s.strip()]


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    paragraphs = [p for p in _PARAGRAPH_SPLIT.split(text) if p.strip()]
    units: List[str] = []
    for p in paragraphs:
        if len(p) <= chunk_size:
            units.append(p)
        else:
            units.extend(_split_sentences(p))

    chunks: List[str] = []
    current = ""
    for unit in units:
        candidate = f"{current} {unit}".strip() if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = (current[-overlap:] + " " + unit).strip()
            # the unit itself might already exceed chunk_size once combined
            # with overlap -- if so, flush it straight away too
            if len(current) > chunk_size:
                chunks.append(current[:chunk_size])
                current = ""
        else:
            # a single unit longer than chunk_size on its own: hard-slice it
            step = max(chunk_size - overlap, 1)
            for i in range(0, len(unit), step):
                chunks.append(unit[i:i + chunk_size])
            current = ""

    if current:
        chunks.append(current)

    return chunks
