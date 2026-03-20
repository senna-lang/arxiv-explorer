"""
recommend.py のセレンディピティロジックのユニットテスト。

テスト対象:
- select_serendipity_papers: スコアバンドフィルタ、重複排除、空リスト
"""

import pytest
import numpy as np
from recommend import select_serendipity_papers, _cosine_similarity


def make_paper(arxiv_id: str, match_score: float, centroid_score: float | None = None) -> dict:
    return {
        "id": arxiv_id,
        "title": f"Paper {arxiv_id}",
        "abstract": "abstract",
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "match_score": match_score,
        "centroid_score": centroid_score if centroid_score is not None else match_score,
        "matched_cluster": "cluster-a",
        "submitted": "2026-03-01",
    }


class TestSelectSerendipityPapers:
    def test_filters_by_score_band(self):
        """スコアバンド [0.45, 0.65] 内の論文のみ返す。"""
        papers = [
            make_paper("001", 0.40),  # 下限未満 → 除外
            make_paper("002", 0.45),  # 下限ちょうど → 含む
            make_paper("003", 0.55),  # 範囲内 → 含む
            make_paper("004", 0.65),  # 上限ちょうど → 含む
            make_paper("005", 0.70),  # 上限超 → 除外
        ]
        result = select_serendipity_papers(papers, min_score=0.45, max_score=0.65, top_n=10, exclude_ids=set())
        ids = [r["id"] for r in result]
        assert "001" not in ids
        assert "002" in ids
        assert "003" in ids
        assert "004" in ids
        assert "005" not in ids

    def test_excludes_duplicate_ids(self):
        """exclude_ids に含まれる論文は除外される。"""
        papers = [
            make_paper("001", 0.55),
            make_paper("002", 0.55),
            make_paper("003", 0.55),
        ]
        result = select_serendipity_papers(papers, 0.45, 0.65, 10, exclude_ids={"001", "003"})
        ids = [r["id"] for r in result]
        assert ids == ["002"]

    def test_top_n_limits_results(self):
        """top_n を超える数は返さない。スコア降順で上位を返す。"""
        papers = [make_paper(str(i), 0.45 + i * 0.02) for i in range(8)]
        result = select_serendipity_papers(papers, 0.45, 0.65, top_n=3, exclude_ids=set())
        assert len(result) == 3
        # スコア降順であること
        scores = [r["match_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_input_returns_empty(self):
        """空リストを渡すと空リストを返す。"""
        result = select_serendipity_papers([], 0.45, 0.65, 10, exclude_ids=set())
        assert result == []

    def test_no_papers_in_band_returns_empty(self):
        """バンド内の論文がゼロの場合は空リストを返す。"""
        papers = [make_paper("001", 0.30), make_paper("002", 0.80)]
        result = select_serendipity_papers(papers, 0.45, 0.65, 10, exclude_ids=set())
        assert result == []


class TestCosineSimlarity:
    def test_identical_vectors(self):
        a = np.array([1.0, 0.0, 0.0])
        assert _cosine_similarity(a, a) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = np.array([1.0, 0.0])
        b = np.array([0.0, 1.0])
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_zero_vector_returns_zero(self):
        a = np.array([0.0, 0.0])
        b = np.array([1.0, 0.0])
        assert _cosine_similarity(a, b) == 0.0
