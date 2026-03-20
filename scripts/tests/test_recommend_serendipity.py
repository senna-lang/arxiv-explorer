"""
scripts/recommend/serendipity.py のユニットテスト

テスト対象:
- select_serendipity_papers: スコアバンドフィルタ、重複排除、top_n 制限
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from recommend.serendipity import select_serendipity_papers


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
        assert "002" in ids and "003" in ids and "004" in ids
        assert "005" not in ids

    def test_excludes_duplicate_ids(self):
        papers = [make_paper("001", 0.55), make_paper("002", 0.55), make_paper("003", 0.55)]
        result = select_serendipity_papers(papers, 0.45, 0.65, 10, exclude_ids={"001", "003"})
        assert [r["id"] for r in result] == ["002"]

    def test_top_n_limits_results(self):
        papers = [make_paper(str(i), 0.45 + i * 0.02) for i in range(8)]
        result = select_serendipity_papers(papers, 0.45, 0.65, top_n=3, exclude_ids=set())
        assert len(result) == 3
        scores = [r["match_score"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_empty_input_returns_empty(self):
        assert select_serendipity_papers([], 0.45, 0.65, 10, exclude_ids=set()) == []

    def test_no_papers_in_band_returns_empty(self):
        papers = [make_paper("001", 0.30), make_paper("002", 0.80)]
        assert select_serendipity_papers(papers, 0.45, 0.65, 10, exclude_ids=set()) == []

    def test_filter_key_centroid_score(self):
        """filter_key='centroid_score' で centroid_score でフィルタできる"""
        papers = [
            make_paper("001", match_score=0.80, centroid_score=0.50),  # centroid in band
            make_paper("002", match_score=0.80, centroid_score=0.30),  # centroid out of band
        ]
        result = select_serendipity_papers(papers, 0.45, 0.65, 10, exclude_ids=set(), filter_key="centroid_score")
        ids = [r["id"] for r in result]
        assert "001" in ids
        assert "002" not in ids
