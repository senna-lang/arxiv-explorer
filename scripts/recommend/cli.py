"""
recommend CLI エントリポイント

ratings.json と map.json から instance-based scoring でおすすめ論文を生成する。

処理フロー:
1. ratings から rating>=min_rating の論文を抽出
2. abstract を allenai/specter2 で Embedding
3. map.json の各クラスタを instance-based scoring で評価
4. ratings 件数に応じて interest_profile スコアと加重合成
5. 上位クラスタ内の論文をスコアリングして recommendations.json に保存

Usage:
  python -m scripts.recommend [--top-clusters N] [--top-n N] [--log]
"""

import argparse
import json
import time
from datetime import datetime
from typing import Any

import numpy as np
from modal_app import app, build_encoder

from core.config import JST, ROOT, load_config
from core.io import append_jsonl, save_json
from core.ratings import load_ratings
from core.similarity import cosine_similarity as _cosine_similarity

from .cluster_ranking import (
    compute_alpha,
    compute_final_score,
    compute_instance_score,
    fetch_papers_for_cluster,
    rank_clusters,
)
from .serendipity import select_serendipity_papers
from .visualization import regenerate_map_html


def main(top_clusters: int, top_n: int, log: bool = False) -> None:
    config = load_config()
    output_dir = ROOT / config["output_dir"]
    model_name: str = config["embedding_model"]
    rec_config: dict = config["recommendation"]
    min_rating: int = rec_config["min_rating"]
    t: dict = config["tuning"]["recommend"]

    started_at = time.time()
    map_path = output_dir / "map.json"

    if not map_path.exists():
        print("[ERROR] map.json not found. Run map_pipeline first.")
        return

    ratings = load_ratings(config)
    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    high_rated = [r for r in ratings if r["rating"] >= min_rating]
    print(f"[INFO] {len(high_rated)} high-rated papers (rating>={min_rating})")

    enc = build_encoder(model_name)

    # 高評価論文のEmbedding: proximity アダプタ（論文↔論文類似度）
    rated_vecs: list[np.ndarray] = []
    if high_rated:
        texts = [f"{r.get('title', '')} [SEP] {r['abstract']}" for r in high_rated]
        vecs = list(enc.encode(texts, adapter="proximity"))
        for r, vec in zip(high_rated, vecs):
            weight = r["rating"] - 1  # ★2→1回、★3→2回
            rated_vecs.extend([vec] * weight)

    # interest_profile のEmbedding: adhoc_query アダプタ（クエリ→論文検索）
    profile_texts: list[str] = config["interest_profile"]
    profile_vecs: list[np.ndarray] = list(enc.encode(profile_texts, adapter="adhoc_query"))

    alpha = compute_alpha(len(high_rated), t["alpha_ratings_threshold"])
    print(f"[INFO] alpha={alpha:.2f} (ratings={len(high_rated)})")

    clusters = map_data["clusters"]
    ranked = rank_clusters(clusters, rated_vecs, profile_vecs, alpha)
    top = ranked[:top_clusters]

    # セレンディピティ: 隣接クラスタ（rank N+1〜）と遠いクラスタ（末尾から）
    ser_n_clusters: int = rec_config.get("serendipity_clusters", 3)
    ser_distant_n: int = rec_config.get("serendipity_distant_clusters", 2)
    ser_top = ranked[top_clusters: top_clusters + ser_n_clusters]
    ser_distant = ranked[max(top_clusters + ser_n_clusters, len(ranked) - ser_distant_n):]

    print(f"[INFO] Top {top_clusters} clusters: {[c['label'] for c in top]}")
    print(f"[INFO] Serendipity adjacent clusters: {[c['label'] for c in ser_top]}")
    print(f"[INFO] Serendipity distant clusters: {[c['label'] for c in ser_distant]}")

    def _score_cluster_papers(cluster_list: list[dict]) -> list[dict]:
        """クラスタ内論文を取得し α-blend スコアを計算する。"""
        candidates: list[dict] = []
        for cluster in cluster_list:
            papers = fetch_papers_for_cluster(cluster["paper_ids"])
            if not papers:
                continue
            texts = [f"{p.title} [SEP] {p.summary}" for p in papers]
            vecs_list: list[np.ndarray] = list(enc.encode(texts, adapter="proximity"))
            centroid = np.array(cluster["centroid"])
            for paper, vec in zip(papers, vecs_list):
                centroid_score = _cosine_similarity(centroid, vec)
                instance = compute_instance_score(vec, rated_vecs)
                profile = compute_instance_score(vec, profile_vecs)
                match_score = compute_final_score(instance, profile, alpha)
                arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
                candidates.append({
                    "id": arxiv_id,
                    "title": paper.title,
                    "abstract": paper.summary,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "match_score": round(match_score, 4),
                    "centroid_score": round(centroid_score, 4),
                    "matched_cluster": cluster["label"],
                    "submitted": paper.published.strftime("%Y-%m-%d"),
                })
        return candidates

    # 上位クラスタ内の論文をスコアリング
    min_match: float = rec_config["min_match_score"]
    recommendations = _score_cluster_papers(top)
    recommendations = [r for r in recommendations if r["centroid_score"] >= min_match]
    recommendations.sort(key=lambda r: r["match_score"], reverse=True)
    recommendations = recommendations[:top_n]

    # セレンディピティ論文
    ser_min_match: float = rec_config.get("serendipity_min_match_score", 0.80)
    ser_top_n: int = rec_config.get("serendipity_top_n", 7)
    ser_distant_top_n: int = rec_config.get("serendipity_distant_top_n", 3)
    rec_ids = {r["id"] for r in recommendations}

    adjacent = select_serendipity_papers(
        _score_cluster_papers(ser_top),
        min_score=ser_min_match, max_score=1.0,
        top_n=ser_top_n, exclude_ids=rec_ids,
        filter_key="centroid_score",
    )
    distant_exclude = rec_ids | {p["id"] for p in adjacent}
    distant = select_serendipity_papers(
        _score_cluster_papers(ser_distant),
        min_score=ser_min_match, max_score=1.0,
        top_n=ser_distant_top_n, exclude_ids=distant_exclude,
        filter_key="centroid_score",
    )
    serendipity = adjacent + distant
    print(f"[INFO] Serendipity papers: {len(adjacent)} adjacent + {len(distant)} distant")

    output: dict[str, Any] = {
        "generated_at": datetime.now(JST).isoformat(),
        "top_clusters": [{"label": c["label"], "score": c["score"]} for c in top],
        "recommendations": recommendations,
        "serendipity_clusters": [
            {"label": c["label"], "score": c["score"]} for c in ser_top + ser_distant
        ],
        "serendipity": serendipity,
    }

    out_path = output_dir / "recommendations.json"
    save_json(out_path, output)
    print(f"[INFO] Saved {len(recommendations)} recommendations to {out_path}")

    if log:
        match_scores = [r["match_score"] for r in recommendations]
        log_entry = {
            "ts": datetime.now(JST).isoformat(),
            "n_ratings": len(high_rated),
            "alpha": round(alpha, 4),
            "top_clusters": [{"label": c["label"], "score": c["score"]} for c in top],
            "n_recommendations": len(recommendations),
            "match_score": {
                "min": round(min(match_scores), 4) if match_scores else None,
                "max": round(max(match_scores), 4) if match_scores else None,
                "mean": round(sum(match_scores) / len(match_scores), 4) if match_scores else None,
            },
            "elapsed_sec": round(time.time() - started_at, 1),
            "model": model_name,
            "tuning": {**t, "min_rating": min_rating, "top_clusters": top_clusters,
                       "top_n": top_n, "min_match_score": rec_config["min_match_score"]},
        }
        append_jsonl(output_dir / "recommend_runs.jsonl", log_entry)
        print("[INFO] Logged to recommend_runs.jsonl")

    # datamapplot で map.html を再生成
    html_path = ROOT / "public" / "map.html"
    regenerate_map_html(map_data, top, ser_top, html_path)


@app.local_entrypoint()
def modal_main(top_clusters: int = 3, top_n: int = 20, log: bool = False) -> None:
    """modal run scripts/recommend/ 用エントリポイント。"""
    main(top_clusters, top_n, log=log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate recommendations from ratings and map")
    parser.add_argument("--top-clusters", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--log", action="store_true",
                        help="Record benchmark metrics to recommend_runs.jsonl")
    args = parser.parse_args()
    main(args.top_clusters, args.top_n, log=args.log)
