"""
fetch_daily パッケージ — arXiv日次収集パイプライン

主なエントリポイント:
- main(date_str, log): fetch → dedup → score → save の一連の処理
"""

from .cli import main
from .dedup import deduplicate, load_seen_ids
from .scoring import score_papers

__all__ = ["main", "deduplicate", "load_seen_ids", "score_papers"]
