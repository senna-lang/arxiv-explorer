"""
セレンディピティ論文選択

提供:
- select_serendipity_papers(...): スコアバンドフィルタ + 重複排除 + top_n 制限
"""


def select_serendipity_papers(
    papers_with_scores: list[dict],
    min_score: float,
    max_score: float,
    top_n: int,
    exclude_ids: set[str],
    filter_key: str = "match_score",
) -> list[dict]:
    """
    filter_key のスコアバンド [min_score, max_score] で絞り込み、上位 top_n を返す。
    exclude_ids に含まれる ID は除外する（recommendations との重複防止）。
    filter_key="centroid_score" を指定するとクラスタ内代表度でフィルタできる。
    """
    filtered = [
        p for p in papers_with_scores
        if min_score <= p[filter_key] <= max_score and p["id"] not in exclude_ids
    ]
    filtered.sort(key=lambda p: p[filter_key], reverse=True)
    return filtered[:top_n]
