"""
scripts/fetch_daily.py のユニットテスト

テスト対象:
- deduplicate: seen_ids にある paper は除外される
- score_papers: α=0 のとき profile_score のみ、α=1 のとき instance_score のみ反映
- load_seen_ids: 過去N日分のJSONから正しくIDを収集
- top_n: スコア降順で指定件数だけ返ることの確認
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fetch_daily import deduplicate, load_seen_ids, score_papers  # re-exported from fetch_daily package


class TestDeduplicate:
    def test_removes_seen_ids(self):
        papers = [
            {"id": "2603.00001"},
            {"id": "2603.00002"},
            {"id": "2603.00003"},
        ]
        seen = {"2603.00001", "2603.00003"}
        result = deduplicate(papers, seen)
        assert len(result) == 1
        assert result[0]["id"] == "2603.00002"

    def test_empty_seen_ids_returns_all(self):
        papers = [{"id": "2603.00001"}, {"id": "2603.00002"}]
        result = deduplicate(papers, set())
        assert len(result) == 2

    def test_all_seen_returns_empty(self):
        papers = [{"id": "2603.00001"}, {"id": "2603.00002"}]
        result = deduplicate(papers, {"2603.00001", "2603.00002"})
        assert result == []

    def test_empty_papers_returns_empty(self):
        result = deduplicate([], {"2603.00001"})
        assert result == []


class TestScorePapers:
    def _make_paper(self, pid: str) -> dict:
        return {"id": pid, "title": "t", "abstract": "a"}

    def test_alpha_zero_uses_profile_only(self):
        """α=0 のとき instance_score は無視されて profile_score のみ反映される"""
        paper = self._make_paper("p1")
        # paper vec と profile vec が同一 → profile_score = 1.0
        # paper vec と rated vec が直交 → instance_score = 0.0
        paper_vec = np.array([1.0, 0.0, 0.0])
        rated_vec = np.array([0.0, 1.0, 0.0])
        profile_vec = np.array([1.0, 0.0, 0.0])

        result = score_papers(
            [paper],
            np.array([paper_vec]),
            [rated_vec],
            [profile_vec],
            alpha=0.0,
            top_n=10,
        )
        assert len(result) == 1
        assert abs(result[0]["score"] - 1.0) < 1e-6

    def test_alpha_one_uses_instance_only(self):
        """α=1 のとき profile_score は無視されて instance_score のみ反映される"""
        paper = self._make_paper("p1")
        # paper vec と rated vec が同一 → instance_score = 1.0
        # paper vec と profile vec が直交 → profile_score = 0.0
        paper_vec = np.array([1.0, 0.0, 0.0])
        rated_vec = np.array([1.0, 0.0, 0.0])
        profile_vec = np.array([0.0, 1.0, 0.0])

        result = score_papers(
            [paper],
            np.array([paper_vec]),
            [rated_vec],
            [profile_vec],
            alpha=1.0,
            top_n=10,
        )
        assert len(result) == 1
        assert abs(result[0]["score"] - 1.0) < 1e-6

    def test_alpha_half_blends_scores(self):
        """α=0.5 のとき instance と profile の平均になる"""
        paper = self._make_paper("p1")
        paper_vec = np.array([1.0, 0.0])
        # instance_score = 1.0 (同一ベクトル)
        rated_vec = np.array([1.0, 0.0])
        # profile_score = 0.0 (直交)
        profile_vec = np.array([0.0, 1.0])

        result = score_papers(
            [paper],
            np.array([paper_vec]),
            [rated_vec],
            [profile_vec],
            alpha=0.5,
            top_n=10,
        )
        assert abs(result[0]["score"] - 0.5) < 1e-6

    def test_sorted_descending_by_score(self):
        """結果はスコア降順でソートされる"""
        papers = [self._make_paper(f"p{i}") for i in range(3)]
        # p0: [1,0] → profile sim = 1.0
        # p1: [0,1] → profile sim = 0.0
        # p2: [0.7,0.7]/norm → profile sim ≈ 0.707
        vecs = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [0.7071, 0.7071],
        ])
        profile_vec = np.array([1.0, 0.0])

        result = score_papers(papers, vecs, [], [profile_vec], alpha=0.0, top_n=10)
        assert result[0]["id"] == "p0"
        assert result[1]["id"] == "p2"
        assert result[2]["id"] == "p1"

    def test_top_n_limits_results(self):
        """top_n 件より多くは返さない"""
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
            [paper],
            np.array([paper_vec]),
            [],  # rated_vecs 空
            [profile_vec],
            alpha=1.0,
            top_n=10,
        )
        assert abs(result[0]["score"] - 0.0) < 1e-6


class TestLoadSeenIds:
    def test_collects_ids_from_json_files(self):
        """過去N日分の YYYYMMDD.json から paper_id を収集する"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # 20260314.json を作成
            data = {
                "papers": [
                    {"id": "2603.00001"},
                    {"id": "2603.00002"},
                ]
            }
            (p / "20260314.json").write_text(json.dumps(data), encoding="utf-8")
            (p / "20260313.json").write_text(
                json.dumps({"papers": [{"id": "2603.00003"}]}), encoding="utf-8"
            )

            ids = load_seen_ids(p, days=30)
            assert "2603.00001" in ids
            assert "2603.00002" in ids
            assert "2603.00003" in ids

    def test_non_date_files_ignored(self):
        """YYYYMMDD.json 以外のファイルは無視される"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            (p / "map.json").write_text(json.dumps({"papers": [{"id": "9999.99999"}]}))
            (p / "ratings.json").write_text(json.dumps({"ratings": []}))
            (p / "20260314.json").write_text(
                json.dumps({"papers": [{"id": "2603.00001"}]})
            )

            ids = load_seen_ids(p, days=30)
            assert "9999.99999" not in ids
            assert "2603.00001" in ids

    def test_empty_directory_returns_empty_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ids = load_seen_ids(Path(tmpdir), days=30)
            assert ids == set()

    def test_days_limit_excludes_old_files(self):
        """days=0 のとき今日分だけを対象とする（古い日付は除外される）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # 未来の日付（今日以降）
            (p / "20260315.json").write_text(
                json.dumps({"papers": [{"id": "new.00001"}]})
            )
            # 古い日付（days=0 なら today のみ）
            (p / "20260101.json").write_text(
                json.dumps({"papers": [{"id": "old.00001"}]})
            )

            ids = load_seen_ids(p, days=0)
            # days=0 → 今日以降のみ含める。20260101 は除外
            assert "old.00001" not in ids
