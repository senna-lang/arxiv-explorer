"""
重複除去ユーティリティ

提供:
- load_seen_ids(output_dir, days): 過去N日分のJSONから paper_id を収集
- deduplicate(papers, seen_ids): 既出IDを除外した論文リストを返す
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from core.config import JST


def load_seen_ids(output_dir: Path, days: int = 30) -> set[str]:
    """
    output_dir 内の過去 days 日分の YYYYMMDD.json から paper_id を収集して返す。
    YYYYMMDD パターンに一致しないファイルは無視する。
    """
    seen: set[str] = set()
    today = datetime.now(JST).date()
    cutoff = today - timedelta(days=days)

    for path in output_dir.glob("????????.json"):
        stem = path.stem
        if not re.match(r"^\d{8}$", stem):
            continue
        try:
            file_date = datetime.strptime(stem, "%Y%m%d").date()
        except ValueError:
            continue
        if file_date < cutoff:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for p in data.get("papers", []):
                if "id" in p:
                    seen.add(p["id"])
        except Exception:
            continue

    return seen


def deduplicate(
    papers: list[dict], seen_ids: set[str]
) -> list[dict]:
    """seen_ids に含まれる paper_id を除外して返す。"""
    return [p for p in papers if p["id"] not in seen_ids]
