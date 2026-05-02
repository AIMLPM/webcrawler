"""Cross-encoder reranker for retrieval pipelines.

Layered on top of an embedding-based first-stage retriever, a cross-encoder
rescores ``(query, candidate)`` pairs to produce a more accurate final
ordering. Cross-encoders see the query and the candidate together (one
forward pass per pair) so they capture interaction signal that bi-encoder
embeddings miss, at the cost of being O(K) instead of O(1) per query.

The default model — ``cross-encoder/ms-marco-MiniLM-L-6-v2`` — is ~22M
parameters, MS-MARCO-trained, and runs CPU-only at <50 ms/query for K=20.

Requires ``pip install markcrawl[ml]`` (``sentence-transformers``). The
model is loaded lazily on first call so importing this module is cheap.
"""

from __future__ import annotations

from typing import List, Optional

from .exceptions import MarkcrawlDependencyError


DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Rerank candidates against a query using a cross-encoder model.

    Typical use::

        reranker = CrossEncoderReranker()
        topk_idx = cosine_top_k(query_vec, chunk_vecs, k=20)
        candidates = [chunks[i].text for i in topk_idx]
        order = reranker.rerank(query, candidates)
        # order is a permutation of range(len(candidates)), best first
        reranked = [topk_idx[j] for j in order]
    """

    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
            except ImportError as exc:
                raise MarkcrawlDependencyError(
                    "Reranking requires sentence-transformers. Install with:\n"
                    "  pip install markcrawl[ml]"
                ) from exc
            self._model = CrossEncoder(self.model_name)
        return self._model

    def score_pairs(self, query: str, candidates: List[str]) -> List[float]:
        """Return the raw cross-encoder score for each candidate, in input order."""
        if not candidates:
            return []
        model = self._load()
        pairs = [(query, c) for c in candidates]
        scores = model.predict(pairs)
        return [float(s) for s in scores]

    def rerank(
        self,
        query: str,
        candidates: List[str],
        top_k: Optional[int] = None,
    ) -> List[int]:
        """Return candidate indices sorted by rerank score, descending.

        Parameters
        ----------
        query:
            The user query.
        candidates:
            Candidate text passages (typically the embedding top-K results).
        top_k:
            If set, return at most ``top_k`` indices. Default ``None``
            returns a full permutation of ``range(len(candidates))``.

        Returns
        -------
        List[int]
            Indices into ``candidates``, sorted by rerank score descending.
        """
        if not candidates:
            return []
        if len(candidates) == 1:
            return [0]
        scores = self.score_pairs(query, candidates)
        # Argsort descending. Stable on ties via the secondary key.
        order = sorted(range(len(candidates)), key=lambda i: scores[i], reverse=True)
        return order if top_k is None else order[:top_k]
