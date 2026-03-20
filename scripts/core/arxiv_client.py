"""
arXiv API ユーティリティ

提供:
- strip_version(entry_id): arXiv entry_id からバージョン番号を除去した ID を返す
- build_category_query(categories): カテゴリリストを arXiv API クエリ文字列に変換する
"""

import re


def strip_version(entry_id: str) -> str:
    """
    arXiv の entry_id からバージョン番号を除去して論文 ID を返す。

    例: "https://arxiv.org/abs/2301.00001v2" → "2301.00001"
         "2301.00001v3" → "2301.00001"
    """
    raw = entry_id.split("/")[-1]
    return re.sub(r"v\d+$", "", raw)


def build_category_query(categories: list[str]) -> str:
    """
    カテゴリリストを arXiv API の OR クエリ文字列に変換する。

    例: ["cs.AI", "cs.LG"] → "cat:cs.AI OR cat:cs.LG"
    """
    return " OR ".join(f"cat:{c}" for c in categories)
