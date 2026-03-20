"""
scripts/recommend/cluster_ranking.py のユニットテスト

テスト対象:
- compute_instance_score: centroid と複数 rated_vecs の cos 類似度平均
- compute_alpha: ratings 件数に応じた α 値計算
- compute_final_score: instance_score と profile_score の α 加重合成
- rank_clusters: クラスタを final_score で降順ソート
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recommend.cluster_ranking import (
    compute_alpha,
    compute_final_score,
    compute_instance_score,
    rank_clusters,
)


class TestComputeInstanceScore:
    def test_identical_vectors_score_one(self):
        v = np.array([1.0, 0.0, 0.0])
        score = compute_instance_score(v, [v, v])
        assert abs(score - 1.0) < 1e-6

    def test_orthogonal_vectors_score_zero(self):
        centroid = np.array([1.0, 0.0, 0.0])
        rated_vecs = [np.array([0.0, 1.0, 0.0])]
        score = compute_instance_score(centroid, rated_vecs)
        assert abs(score) < 1e-6

    def test_empty_rated_vecs_returns_zero(self):
        centroid = np.array([1.0, 0.0, 0.0])
        assert compute_instance_score(centroid, []) == 0.0

    def test_returns_float(self):
        v = np.array([1.0, 0.0])
        assert isinstance(compute_instance_score(v, [v]), float)


class TestComputeAlpha:
    def test_zero_ratings_returns_zero(self):
        assert compute_alpha(0, 50) == 0.0

    def test_threshold_ratings_returns_one(self):
        assert compute_alpha(50, 50) == 1.0

    def test_above_threshold_capped_at_one(self):
        assert compute_alpha(100, 50) == 1.0

    def test_half_threshold_returns_half(self):
        assert abs(compute_alpha(25, 50) - 0.5) < 1e-6


class TestComputeFinalScore:
    def test_alpha_zero_returns_profile(self):
        assert compute_final_score(1.0, 0.5, alpha=0.0) == 0.5

    def test_alpha_one_returns_instance(self):
        assert compute_final_score(0.8, 0.2, alpha=1.0) == 0.8

    def test_alpha_half_returns_mean(self):
        assert abs(compute_final_score(1.0, 0.0, alpha=0.5) - 0.5) < 1e-6


class TestRankClusters:
    def _make_cluster(self, cid: int, centroid: list[float]) -> dict:
        return {"id": cid, "centroid": centroid, "label": f"cluster-{cid}", "keywords": []}

    def test_sorted_descending_by_score(self):
        # cluster 0: centroid=[1,0] → profile_score=1.0 (alpha=0)
        # cluster 1: centroid=[0,1] → profile_score=0.0
        clusters = [
            self._make_cluster(0, [1.0, 0.0]),
            self._make_cluster(1, [0.0, 1.0]),
        ]
        profile_vecs = [np.array([1.0, 0.0])]
        ranked = rank_clusters(clusters, rated_vecs=[], profile_vecs=profile_vecs, alpha=0.0)
        assert ranked[0]["id"] == 0
        assert ranked[1]["id"] == 1

    def test_score_field_added(self):
        clusters = [self._make_cluster(0, [1.0, 0.0])]
        ranked = rank_clusters(clusters, [], [np.array([1.0, 0.0])], alpha=0.0)
        assert "score" in ranked[0]

    def test_empty_clusters_returns_empty(self):
        assert rank_clusters([], [], [], alpha=0.5) == []
