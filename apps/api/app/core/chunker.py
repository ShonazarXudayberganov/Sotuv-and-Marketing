"""Token-aware text chunker for RAG ingestion.

Heuristic: ~4 chars per token (English/Latin), fall back to ~3 for Cyrillic.
We split on paragraph boundaries first, then sentences, then hard-cut at the
window size. Each chunk has a configurable overlap with the next so context
isn't lost at the seams.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_CHUNK_TOKENS = 500
DEFAULT_OVERLAP_TOKENS = 80


@dataclass(slots=True)
class Chunk:
    position: int
    content: str
    token_count: int


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    cyrillic = sum(1 for ch in text if "Ѐ" <= ch <= "ӿ")
    ratio = 3 if cyrillic > len(text) // 3 else 4
    return max(1, len(text) // ratio)


_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZА-ЯЎҚҒҲ])")  # noqa: RUF001


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in _PARAGRAPH_RE.split(text) if p.strip()]


def _split_sentences(paragraph: str) -> list[str]:
    parts = [s.strip() for s in _SENTENCE_RE.split(paragraph) if s.strip()]
    return parts or [paragraph]


def chunk_text(
    text: str,
    *,
    target_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Split ``text`` into ~target_tokens windows with overlap_tokens carryover."""
    text = text.strip()
    if not text:
        return []

    units: list[tuple[str, int]] = []
    for paragraph in _split_paragraphs(text):
        for sentence in _split_sentences(paragraph):
            units.append((sentence, estimate_tokens(sentence)))

    if not units:
        return []

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_tokens = 0
    position = 0

    def flush() -> None:
        nonlocal buf, buf_tokens, position
        if not buf:
            return
        content = " ".join(buf).strip()
        chunks.append(Chunk(position=position, content=content, token_count=buf_tokens))
        position += 1
        if overlap_tokens > 0 and buf_tokens > overlap_tokens:
            tail: list[str] = []
            tail_tokens = 0
            for unit in reversed(buf):
                t = estimate_tokens(unit)
                if tail_tokens + t > overlap_tokens:
                    break
                tail.insert(0, unit)
                tail_tokens += t
            buf = tail
            buf_tokens = tail_tokens
        else:
            buf = []
            buf_tokens = 0

    for sentence, tok in units:
        if tok > target_tokens:
            # Hard cut a too-long sentence into character windows.
            step = target_tokens * 4
            for i in range(0, len(sentence), step):
                slice_ = sentence[i : i + step]
                buf.append(slice_)
                buf_tokens += estimate_tokens(slice_)
                if buf_tokens >= target_tokens:
                    flush()
            continue

        if buf_tokens + tok > target_tokens and buf:
            flush()
        buf.append(sentence)
        buf_tokens += tok

    flush()
    return chunks
