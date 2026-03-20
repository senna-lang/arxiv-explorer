"""
scripts/recommend.py のユニットテスト

テスト対象:
- compute_instance_score: centroidと複数rated_vecsのcos類似度平均
- compute_alpha: ratings件数に応じたα値計算
- compute_final_score: instance_scoreとprofile_scoreのα加重合成
- rank_clusters: クラスタをfinal_scoreで降順ソート
"""

import sys
import os

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recommend import compute_instance_score, compute_alpha, compute_final_score, rank_clusters  # re-exported from recommend package


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

    def test_average_of_similarities(self):
        centroid = np.array([1.0, 0.0, 0.0])
        v1 = np.array([1.0, 0.0, 0.0])   # cos_sim = 1.0
        v2 = np.array([0.0, 1.0, 0.0])   # cos_sim = 0.0
        score = compute_instance_score(centroid, [v1, v2])
        assert abs(score - 0.5) < 1e-6

    def test_empty_rated_vecs_returns_zero(self):
        centroid = np.array([1.0, 0.0, 0.0])
        score = compute_instance_score(centroid, [])
        assert score == 0.0


class TestComputeAlpha:
    def test_zero_ratings_returns_zero(self):
        assert compute_alpha(0, 50) == 0.0

    def test_fifty_ratings_returns_one(self):
        assert compute_alpha(50, 50) == 1.0

    def test_over_fifty_capped_at_one(self):
        assert compute_alpha(100, 50) == 1.0

    def test_twenty_five_returns_half(self):
        assert abs(compute_alpha(25, 50) - 0.5) < 1e-6

    def test_monotonically_increasing(self):
        alphas = [compute_alpha(n, 50) for n in range(0, 55, 5)]
        assert all(a <= b for a, b in zip(alphas, alphas[1:]))


class TestComputeFinalScore:
    def test_alpha_zero_uses_only_profile(self):
        score = compute_final_score(instance=0.9, profile=0.3, alpha=0.0)
        assert abs(score - 0.3) < 1e-6

    def test_alpha_one_uses_only_instance(self):
        score = compute_final_score(instance=0.9, profile=0.3, alpha=1.0)
        assert abs(score - 0.9) < 1e-6

    def test_alpha_half_is_average(self):
        score = compute_final_score(instance=0.8, profile=0.4, alpha=0.5)
        assert abs(score - 0.6) < 1e-6


class TestRankClusters:
    def _make_cluster(self, label: str, centroid: np.ndarray) -> dict:
        return {"label": label, "centroid": centroid.tolist(), "id": 0, "keywords": [], "paper_ids": [], "size": 0, "umap_x": 0.0, "umap_y": 0.0}

    def test_sorted_descending_by_score(self):
        c1 = self._make_cluster("a", np.array([1.0, 0.0, 0.0]))
        c2 = self._make_cluster("b", np.array([0.0, 1.0, 0.0]))
        c3 = self._make_cluster("c", np.array([0.7, 0.7, 0.0]))

        rated_vecs = [np.array([1.0, 0.0, 0.0])]  # cluster "a"と完全一致
        profile_vecs = [np.array([1.0, 0.0, 0.0])]

        ranked = rank_clusters([c1, c2, c3], rated_vecs, profile_vecs, alpha=1.0)
        assert ranked[0]["label"] == "a"

    def test_returns_all_clusters(self):
        clusters = [self._make_cluster(str(i), np.array([1.0, 0.0])) for i in range(5)]
        rated_vecs = [np.array([1.0, 0.0])]
        profile_vecs = [np.array([1.0, 0.0])]
        ranked = rank_clusters(clusters, rated_vecs, profile_vecs, alpha=0.5)
        assert len(ranked) == 5

    def test_each_item_has_score_field(self):
        clusters = [self._make_cluster("x", np.array([1.0, 0.0]))]
        rated_vecs = [np.array([1.0, 0.0])]
        profile_vecs = [np.array([1.0, 0.0])]
        ranked = rank_clusters(clusters, rated_vecs, profile_vecs, alpha=0.5)
        assert "score" in ranked[0]
