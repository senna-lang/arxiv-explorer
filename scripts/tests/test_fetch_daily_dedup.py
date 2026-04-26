"""
scripts/fetch_daily/dedup.py のユニットテスト

テスト対象:
- load_seen_ids: 過去N日分のJSONから paper_id を収集
- deduplicate: seen_ids にある論文を除外
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import JST
from fetch_daily.dedup import deduplicate, load_seen_ids


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


class TestLoadSeenIds:
    def test_collects_ids_from_json_files(self, tmp_path: Path):
        today = datetime.now(JST).date()
        recent_a = today.strftime("%Y%m%d")
        recent_b = (today - timedelta(days=1)).strftime("%Y%m%d")
        data = {"papers": [{"id": "2603.00001"}, {"id": "2603.00002"}]}
        (tmp_path / f"{recent_a}.json").write_text(json.dumps(data), encoding="utf-8")
        (tmp_path / f"{recent_b}.json").write_text(
            json.dumps({"papers": [{"id": "2603.00003"}]}), encoding="utf-8"
        )

        ids = load_seen_ids(tmp_path, days=30)
        assert "2603.00001" in ids
        assert "2603.00002" in ids
        assert "2603.00003" in ids

    def test_non_date_files_ignored(self, tmp_path: Path):
        today_str = datetime.now(JST).date().strftime("%Y%m%d")
        (tmp_path / "map.json").write_text(json.dumps({"papers": [{"id": "9999.99999"}]}))
        (tmp_path / "ratings.json").write_text(json.dumps({"ratings": []}))
        (tmp_path / f"{today_str}.json").write_text(
            json.dumps({"papers": [{"id": "2603.00001"}]})
        )

        ids = load_seen_ids(tmp_path, days=30)
        assert "9999.99999" not in ids
        assert "2603.00001" in ids

    def test_empty_directory_returns_empty_set(self, tmp_path: Path):
        ids = load_seen_ids(tmp_path, days=30)
        assert ids == set()

    def test_days_limit_excludes_old_files(self, tmp_path: Path):
        today = datetime.now(JST).date()
        today_str = today.strftime("%Y%m%d")
        old_str = (today - timedelta(days=120)).strftime("%Y%m%d")
        (tmp_path / f"{today_str}.json").write_text(
            json.dumps({"papers": [{"id": "new.00001"}]})
        )
        (tmp_path / f"{old_str}.json").write_text(
            json.dumps({"papers": [{"id": "old.00001"}]})
        )

        ids = load_seen_ids(tmp_path, days=0)
        assert "old.00001" not in ids
        assert "new.00001" in ids
