"""Embeddings service.

Uses the tenant's stored OpenAI credentials (via integration_service). When no
credentials are set OR running in tests/dev with ``EMBEDDINGS_MOCK=true``,
falls back to a deterministic hash-based embedding so the rest of the RAG
pipeline keeps working without spending API budget.
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
from collections.abc import Sequence

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import EMBEDDING_DIM
from app.services.integration_service import get_credentials

logger = logging.getLogger(__name__)

OPENAI_EMBED_MODEL = "text-embedding-3-small"
OPENAI_URL = "https://api.openai.com/v1/embeddings"


def _is_mock_mode() -> bool:
    return os.getenv("EMBEDDINGS_MOCK", "false").lower() in {"1", "true", "yes"}


def deterministic_embedding(text: str, *, dim: int = EMBEDDING_DIM) -> list[float]:
    """Hash-based pseudo-embedding for tests / no-credentials fallback.

    Same text always returns the same vector. Cosine similarity between texts
    is meaningful enough for unit tests though it has no real semantics.
    """
    seed = hashlib.sha512(text.encode("utf-8")).digest()
    out: list[float] = []
    i = 0
    while len(out) < dim:
        if i >= len(seed):
            seed = hashlib.sha512(seed).digest()
            i = 0
        byte = seed[i]
        # Map [0..255] to [-1, 1]
        out.append((byte / 127.5) - 1.0)
        i += 1
    # L2-normalize so cosine similarity behaves
    norm = math.sqrt(sum(v * v for v in out)) or 1.0
    return [v / norm for v in out]


async def _openai_embed(api_key: str, texts: Sequence[str]) -> list[list[float]]:
    payload = {"model": OPENAI_EMBED_MODEL, "input": list(texts)}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60) as http:
        resp = await http.post(OPENAI_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return [d["embedding"] for d in data["data"]]


async def embed_texts(db: AsyncSession, texts: Sequence[str]) -> list[list[float]]:
    """Embed each text, falling back to deterministic mode when needed."""
    if not texts:
        return []

    if _is_mock_mode():
        return [deterministic_embedding(t) for t in texts]

    creds = await get_credentials(db, "openai")
    api_key = (creds or {}).get("api_key") if creds else None
    if not api_key:
        logger.warning("OpenAI credentials not configured — using deterministic embeddings")
        return [deterministic_embedding(t) for t in texts]

    try:
        return await _openai_embed(str(api_key), texts)
    except (httpx.HTTPError, KeyError) as exc:
        logger.warning("OpenAI embeddings call failed (%s) — falling back to mock", exc)
        return [deterministic_embedding(t) for t in texts]
