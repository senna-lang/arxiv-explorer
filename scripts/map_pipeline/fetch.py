"""
arXiv API から論文を取得するモジュール（キャッシュ付き）

提供:
- fetch_arxiv_papers(categories, max_papers, cache_dir): 当日中キャッシュ付きで論文取得
"""

import hashlib
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import arxiv

from core.arxiv_client import build_category_query
from core.config import JST


def fetch_arxiv_papers(
    categories: list[str], max_papers: int, cache_dir: Path
) -> list[Any]:
    """arXiv API で対象カテゴリの論文を取得する。結果は当日中キャッシュする。"""
    today = datetime.now(JST).strftime("%Y%m%d")
    key = hashlib.md5(f"{sorted(categories)}{max_papers}".encode()).hexdigest()[:8]
    cache_path = cache_dir / f"arxiv_{today}_{key}.pkl"

    if cache_path.exists():
        print(f"[INFO] Loading from cache: {cache_path.name}")
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    client = arxiv.Client(page_size=500, num_retries=3)
    query = build_category_query(categories)
    search = arxiv.Search(
        query=query,
        max_results=max_papers,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    results = list(client.results(search))

    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(results, f)
    print(f"[INFO] Cached {len(results)} papers to {cache_path.name}")
    return results
