"""Tests for markcrawl.retrieval — cross-encoder reranker.

The cross-encoder model itself is a pre-trained NN that's expensive to
download in CI; these tests inject a fake model into the reranker via
``_model`` so the rerank logic is testable without the real model.
"""

from __future__ import annotations

import pytest

from markcrawl.exceptions import MarkcrawlDependencyError
from markcrawl.retrieval import DEFAULT_RERANKER_MODEL, CrossEncoderReranker


class FakeModel:
    """Stub cross-encoder. Returns predetermined scores keyed by candidate text."""

    def __init__(self, scores_by_candidate: dict[str, float]):
        self.scores_by_candidate = scores_by_candidate
        self.calls: list[list[tuple[str, str]]] = []

    def predict(self, pairs):
        self.calls.append(list(pairs))
        return [self.scores_by_candidate[c] for (_, c) in pairs]


class TestCrossEncoderReranker:
    def test_default_model_name(self):
        r = CrossEncoderReranker()
        assert r.model_name == DEFAULT_RERANKER_MODEL
        assert r._model is None  # lazy

    def test_custom_model_name(self):
        r = CrossEncoderReranker(model_name="some/other-model")
        assert r.model_name == "some/other-model"

    def test_empty_candidates_returns_empty(self):
        r = CrossEncoderReranker()
        assert r.rerank("any query", []) == []
        assert r.score_pairs("any query", []) == []
        # Model should not have been loaded
        assert r._model is None

    def test_single_candidate_returns_zero(self):
        r = CrossEncoderReranker()
        assert r.rerank("any query", ["only one"]) == [0]
        # Model should not have been loaded for a single-candidate shortcut
        assert r._model is None

    def test_rerank_returns_indices_in_score_descending_order(self):
        candidates = ["a", "b", "c", "d"]
        scores = {"a": 0.1, "b": 0.9, "c": 0.5, "d": 0.7}
        r = CrossEncoderReranker()
        r._model = FakeModel(scores)
        order = r.rerank("q", candidates)
        # Expected order: b (0.9), d (0.7), c (0.5), a (0.1)
        assert order == [1, 3, 2, 0]

    def test_rerank_top_k_truncates(self):
        candidates = ["a", "b", "c", "d"]
        scores = {"a": 0.1, "b": 0.9, "c": 0.5, "d": 0.7}
        r = CrossEncoderReranker()
        r._model = FakeModel(scores)
        order = r.rerank("q", candidates, top_k=2)
        assert order == [1, 3]

    def test_rerank_top_k_larger_than_candidates(self):
        candidates = ["a", "b"]
        scores = {"a": 0.5, "b": 0.9}
        r = CrossEncoderReranker()
        r._model = FakeModel(scores)
        order = r.rerank("q", candidates, top_k=10)
        assert order == [1, 0]

    def test_rerank_returns_permutation(self):
        candidates = [f"c{i}" for i in range(5)]
        scores = {f"c{i}": float(i % 3) for i in range(5)}
        r = CrossEncoderReranker()
        r._model = FakeModel(scores)
        order = r.rerank("q", candidates)
        assert sorted(order) == list(range(5))

    def test_score_pairs_returns_floats_in_input_order(self):
        candidates = ["a", "b", "c"]
        scores = {"a": 0.3, "b": 0.7, "c": 0.5}
        r = CrossEncoderReranker()
        r._model = FakeModel(scores)
        result = r.score_pairs("q", candidates)
        assert result == [0.3, 0.7, 0.5]
        assert all(isinstance(s, float) for s in result)

    def test_score_pairs_passes_query_through_to_model(self):
        candidates = ["a", "b"]
        scores = {"a": 0.1, "b": 0.2}
        fake = FakeModel(scores)
        r = CrossEncoderReranker()
        r._model = fake
        r.score_pairs("my query", candidates)
        assert fake.calls == [[("my query", "a"), ("my query", "b")]]

    def test_lazy_load_only_once(self):
        candidates = ["a", "b"]
        scores = {"a": 0.1, "b": 0.2}
        fake = FakeModel(scores)
        r = CrossEncoderReranker()
        r._model = fake
        r.rerank("q", candidates)
        r.rerank("q", candidates)
        # Two predict calls but the model was injected, not (re)constructed.
        assert len(fake.calls) == 2

    def test_missing_dependency_raises_clear_error(self, monkeypatch):
        # Simulate sentence_transformers not installed by making the
        # import inside _load() fail. We patch builtins.__import__ to
        # raise ImportError when sentence_transformers is requested.
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                raise ImportError("No module named 'sentence_transformers'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        r = CrossEncoderReranker()
        with pytest.raises(MarkcrawlDependencyError, match="markcrawl\\[ml\\]"):
            r.rerank("q", ["a", "b"])

    def test_ties_produce_stable_order(self):
        # Identical scores should resolve to input-order (stable sort).
        candidates = ["a", "b", "c"]
        scores = {"a": 0.5, "b": 0.5, "c": 0.5}
        r = CrossEncoderReranker()
        r._model = FakeModel(scores)
        order = r.rerank("q", candidates)
        assert order == [0, 1, 2]

    def test_exposed_from_package_root(self):
        # Sanity check that the public re-export from markcrawl/__init__.py
        # works — callers can use ``from markcrawl import CrossEncoderReranker``.
        from markcrawl import CrossEncoderReranker as TopLevel
        assert TopLevel is CrossEncoderReranker
