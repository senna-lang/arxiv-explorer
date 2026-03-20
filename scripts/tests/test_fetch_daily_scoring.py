"""
scripts/fetch_daily/scoring.py のユニットテスト

テスト対象:
- score_papers: α-blend スコア計算・降順ソート・top_n 制限
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetch_daily.scoring import score_papers


class TestScorePapers:
    def _make_paper(self, pid: str) -> dict:
        return {"id": pid, "title": "t", "abstract": "a"}

    def test_alpha_zero_uses_profile_only(self):
        """α=0 のとき instance_score は無視されて profile_score のみ反映される"""
        paper = self._make_paper("p1")
        paper_vec = np.array([1.0, 0.0, 0.0])
        rated_vec = np.array([0.0, 1.0, 0.0])
        profile_vec = np.array([1.0, 0.0, 0.0])

        result = score_papers(
            [paper], np.array([paper_vec]), [rated_vec], [profile_vec],
            alpha=0.0, top_n=10,
        )
        assert len(result) == 1
        assert abs(result[0]["score"] - 1.0) < 1e-6

    def test_alpha_one_uses_instance_only(self):
        """α=1 のとき profile_score は無視されて instance_score のみ反映される"""
        paper = self._make_paper("p1")
        paper_vec = np.array([1.0, 0.0, 0.0])
        rated_vec = np.array([1.0, 0.0, 0.0])
        profile_vec = np.array([0.0, 1.0, 0.0])

        result = score_papers(
            [paper], np.array([paper_vec]), [rated_vec], [profile_vec],
            alpha=1.0, top_n=10,
        )
        assert abs(result[0]["score"] - 1.0) < 1e-6

    def test_alpha_half_blends_scores(self):
        """α=0.5 のとき instance と profile の平均になる"""
        paper = self._make_paper("p1")
        paper_vec = np.array([1.0, 0.0])
        rated_vec = np.array([1.0, 0.0])   # instance_score = 1.0
        profile_vec = np.array([0.0, 1.0]) # profile_score = 0.0

        result = score_papers(
            [paper], np.array([paper_vec]), [rated_vec], [profile_vec],
            alpha=0.5, top_n=10,
        )
        assert abs(result[0]["score"] - 0.5) < 1e-6

    def test_sorted_descending_by_score(self):
        papers = [self._make_paper(f"p{i}") for i in range(3)]
        vecs = np.array([[1.0, 0.0], [0.0, 1.0], [0.7071, 0.7071]])
        profile_vec = np.array([1.0, 0.0])

        result = score_papers(papers, vecs, [], [profile_vec], alpha=0.0, top_n=10)
        assert result[0]["id"] == "p0"
        assert result[1]["id"] == "p2"
        assert result[2]["id"] == "p1"

    def test_top_n_limits_results(self):
        papers = [self._make_paper(f"p{i}") for i in range(5)]
        vecs = np.eye(5)
        profile_vec = np.array([1.0, 0.0, 0.0, 0.0, 0.0])

        result = score_papers(papers, vecs, [], [profile_vec], alpha=0.0, top_n=3)
        assert len(result) == 3

    def test_no_rated_vecs_with_alpha_one_returns_zero(self):
        """rated_vecs が空で α=1 のとき instance_score は 0.0"""
        paper = self._make_paper("p1")
        paper_vec = np.array([1.0, 0.0])
        profile_vec = np.array([1.0, 0.0])

        result = score_papers(
            [paper], np.array([paper_vec]), [], [profile_vec],
            alpha=1.0, top_n=10,
        )
        assert abs(result[0]["score"] - 0.0) < 1e-6
