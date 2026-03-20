"""
scripts/core/similarity.py のユニットテスト

テスト対象:
- cosine_similarity: 2ベクトルのcos類似度
- mean_cosine_similarity: 1ベクトル vs 複数ベクトルの類似度平均
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.similarity import cosine_similarity, mean_cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        v = np.array([1.0, 0.0, 0.0])
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors_score_zero(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        assert abs(cosine_similarity(a, b)) < 1e-6

    def test_opposite_vectors_score_minus_one(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([-1.0, 0.0, 0.0])
        assert abs(cosine_similarity(a, b) + 1.0) < 1e-6

    def test_zero_vector_returns_zero(self):
        a = np.array([0.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        assert cosine_similarity(a, b) == 0.0
        assert cosine_similarity(b, a) == 0.0

    def test_both_zero_vectors_returns_zero(self):
        a = np.array([0.0, 0.0, 0.0])
        assert cosine_similarity(a, a) == 0.0

    def test_returns_float(self):
        v = np.array([1.0, 2.0, 3.0])
        result = cosine_similarity(v, v)
        assert isinstance(result, float)


class TestMeanCosineSimilarity:
    def test_single_identical_vector_returns_one(self):
        v = np.array([1.0, 0.0, 0.0])
        assert abs(mean_cosine_similarity(v, [v]) - 1.0) < 1e-6

    def test_multiple_vectors_returns_mean(self):
        v = np.array([1.0, 0.0, 0.0])
        a = np.array([1.0, 0.0, 0.0])  # sim = 1.0
        b = np.array([0.0, 1.0, 0.0])  # sim = 0.0
        result = mean_cosine_similarity(v, [a, b])
        assert abs(result - 0.5) < 1e-6

    def test_empty_list_returns_zero(self):
        v = np.array([1.0, 0.0, 0.0])
        assert mean_cosine_similarity(v, []) == 0.0

    def test_returns_float(self):
        v = np.array([1.0, 2.0, 3.0])
        result = mean_cosine_similarity(v, [v])
        assert isinstance(result, float)
