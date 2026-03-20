"""
arXiv API から論文を取得するモジュール

提供:
- fetch_recent_papers(config, max_candidates): 最新論文をカテゴリ横断で取得
"""

import re
from typing import Any

import arxiv

from core.arxiv_client import build_category_query, strip_version


def fetch_recent_papers(
    config: dict[str, Any], max_candidates: int
) -> list[dict[str, Any]]:
    """
    arXiv APIで config.categories の各カテゴリから最新 max_candidates 件を取得する。
    日付フィルタは使わない（週末・祝日はarXivが更新しないため、固定日数だと0件になる）。
    重複除去は呼び出し元の deduplicate() に委ねる。
    """
    categories: list[str] = config["categories"]
    query = build_category_query(categories)

    client = arxiv.Client(page_size=200, num_retries=3)
    search = arxiv.Search(
        query=query,
        max_results=max_candidates,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers: list[dict[str, Any]] = []
    for result in client.results(search):
        if len(papers) >= max_candidates:
            break

        arxiv_id = strip_version(result.entry_id)

        github_match = re.search(r"https?://github\.com/[^\s\)]+", result.summary)
        github_url = github_match.group(0) if github_match else None

        paper: dict[str, Any] = {
            "id": arxiv_id,
            "title": result.title,
            "authors": [a.name for a in result.authors],
            "abstract": result.summary,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "categories": result.categories,
            "submitted": result.published.strftime("%Y-%m-%d"),
        }
        if github_url:
            paper["github_url"] = github_url

        papers.append(paper)

    return papers
