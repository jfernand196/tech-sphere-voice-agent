"""Embedding backends for RAG (DIP): fastembed semantic vs deterministic hash."""

from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache
from typing import List, Protocol, Sequence, runtime_checkable

# Built-in in fastembed 0.3.6; multilingual (~50 langs), 384-d, ~220 MB.
# (intfloat/multilingual-e5-small is not in the 0.3.6 registry.)
DEFAULT_FASTEMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
HASH_DIMS = 256


@runtime_checkable
class Embedder(Protocol):
    name: str
    dim: int

    def embed_query(self, text: str) -> List[float]: ...

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]: ...

    def warmup(self) -> None: ...


def tokenize(text: str) -> List[str]:
    """Shared Spanish-aware tokenizer for hash embeddings and BM25."""
    return re.findall(r"[a-záéíóúñü0-9]+", text.lower())


def hash_embed_text(text: str, dims: int = HASH_DIMS) -> List[float]:
    """Deterministic bag-of-tokens embedding (offline fallback / fast tests)."""
    vec = [0.0] * dims
    tokens = tokenize(text)
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class HashEmbedder:
    """No external model — used in unit tests and EMBED_PROVIDER=hash."""

    name = "hash"
    dim = HASH_DIMS

    def embed_query(self, text: str) -> List[float]:
        return hash_embed_text(text, self.dim)

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        return [hash_embed_text(t, self.dim) for t in texts]

    def warmup(self) -> None:
        _ = self.embed_query("warmup")


class FastembedEmbedder:
    """ONNX multilingual MiniLM via fastembed (CPU, no torch)."""

    def __init__(self, model_name: str = DEFAULT_FASTEMBED_MODEL) -> None:
        # Include pooling tag so embed_meta invalidates older CLS vectors (fastembed≥0.6).
        self.name = f"fastembed:{model_name}:mean"
        self.dim = 384
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self._model_name)
            # Confirm dim from first tiny embed if registry differs.
            probe = list(self._model.query_embed("dim-probe"))
            if probe:
                self.dim = int(len(probe[0]))
        return self._model

    def warmup(self) -> None:
        _ = self._get_model()
        _ = self.embed_query("warmup")

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        vectors = list(model.query_embed(text or " "))
        if not vectors:
            return [0.0] * self.dim
        return [float(x) for x in vectors[0]]

    def embed_documents(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        # passage_embed is the retrieval-oriented path when available.
        if hasattr(model, "passage_embed"):
            raw = list(model.passage_embed(list(texts)))
        else:
            raw = list(model.embed(list(texts)))
        out: List[List[float]] = []
        for vec in raw:
            out.append([float(x) for x in vec])
        # Keep alignment if the generator short-circuits empty strings.
        while len(out) < len(texts):
            out.append([0.0] * self.dim)
        return out[: len(texts)]


def build_embedder(provider: str) -> Embedder:
    """Factory: fastembed (default) | hash."""
    key = (provider or "fastembed").strip().lower()
    if key in {"hash", "mock"}:
        return HashEmbedder()
    if key in {"fastembed", "minilm"}:
        return FastembedEmbedder()
    raise ValueError(
        f"Unknown EMBED_PROVIDER={provider!r}. Use 'fastembed' or 'hash'."
    )


@lru_cache
def get_embedder(provider: str) -> Embedder:
    return build_embedder(provider)
