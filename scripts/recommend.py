"""
ratings.jsonとmap.jsonからinstance-based scoringでおすすめ論文を生成する。

処理フロー:
1. ratings.jsonからrating>=min_ratingの論文を抽出
2. abstractをallenai/specter2でEmbedding（再計算）
3. map.jsonの各クラスタをinstance-based scoringで評価
   score(c) = mean(cos_sim(centroid_c, v_i) for v_i in rated_vecs)
4. ratings件数に応じてinterest_profileスコアと加重合成
   α = min(1.0, 件数/50)
   final = α * instance_score + (1-α) * profile_score
5. 上位クラスタ内の論文をスコアリングしてrecommendations.jsonに保存

実行:
    python scripts/recommend.py
    python scripts/recommend.py --top-clusters 3 --top-n 20
"""

import argparse
import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import arxiv
import numpy as np
from sentence_transformers import SentenceTransformer

JST = ZoneInfo("Asia/Tokyo")
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """2ベクトルのcos類似度を返す。ゼロベクトルは0.0として扱う。"""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_instance_score(centroid: np.ndarray, rated_vecs: list[np.ndarray]) -> float:
    """
    クラスタcentroidと高評価論文ベクトル群のcos類似度平均を返す。
    rated_vecsが空の場合は0.0。
    """
    if not rated_vecs:
        return 0.0
    sims = [_cosine_similarity(centroid, v) for v in rated_vecs]
    return float(np.mean(sims))


def compute_alpha(n_ratings: int) -> float:
    """
    ratings件数に応じたα値を返す。
    0件=0.0、50件以上=1.0、線形補間。
    """
    return min(1.0, n_ratings / 50)


def compute_final_score(instance: float, profile: float, alpha: float) -> float:
    """
    instance_scoreとprofile_scoreをα加重合成する。
    final = α * instance + (1-α) * profile
    """
    return alpha * instance + (1 - alpha) * profile


def rank_clusters(
    clusters: list[dict[str, Any]],
    rated_vecs: list[np.ndarray],
    profile_vecs: list[np.ndarray],
    alpha: float,
) -> list[dict[str, Any]]:
    """
    クラスタリストをfinal_scoreで降順ソートして返す。
    各クラスタにscoreフィールドを追加する。
    """
    scored = []
    for cluster in clusters:
        centroid = np.array(cluster["centroid"])
        instance = compute_instance_score(centroid, rated_vecs)
        profile = compute_instance_score(centroid, profile_vecs)
        score = compute_final_score(instance, profile, alpha)
        scored.append({**cluster, "score": round(score, 4)})
    return sorted(scored, key=lambda c: c["score"], reverse=True)


def fetch_papers_for_cluster(paper_ids: list[str]) -> list[Any]:
    """クラスタ内のarXiv IDで論文情報を取得する。"""
    if not paper_ids:
        return []
    client = arxiv.Client()
    search = arxiv.Search(id_list=paper_ids[:100])  # API制限のため上限100
    return list(client.results(search))


def main(top_clusters: int, top_n: int) -> None:
    config = load_config()
    output_dir = ROOT / config["output_dir"]
    model_name: str = config["embedding_model"]
    rec_config: dict = config["recommendation"]
    min_rating: int = rec_config["min_rating"]

    map_path = output_dir / "map.json"

    if not map_path.exists():
        print("[ERROR] map.json not found. Run map.py first.")
        return

    # ratings取得: ratings_urlが設定されていればHTTP(Cloudflare KV)、なければローカルファイル
    ratings_url: str = config.get("ratings_url", "")
    if ratings_url:
        print(f"[INFO] Fetching ratings from {ratings_url}")
        with urllib.request.urlopen(ratings_url) as res:
            ratings_data = json.loads(res.read())
    else:
        ratings_path = output_dir / "ratings.json"
        with open(ratings_path, encoding="utf-8") as f:
            ratings_data = json.load(f)
    with open(map_path, encoding="utf-8") as f:
        map_data = json.load(f)

    # min_rating以上の論文だけを対象にする（デフォルト: 星2以上）
    high_rated = [r for r in ratings_data["ratings"] if r["rating"] >= min_rating]
    print(f"[INFO] {len(high_rated)} high-rated papers (rating>={min_rating})")

    model = SentenceTransformer(model_name)

    # 高評価論文のEmbedding: ★3は★2の2倍の重みで rated_vecs に追加
    # 重み付けは同一ベクトルを複数回追加することで実現（★2→1回、★3→2回）
    rated_vecs: list[np.ndarray] = []
    if high_rated:
        abstracts = [r["abstract"] for r in high_rated]
        vecs = list(model.encode(abstracts, show_progress_bar=False))
        for r, vec in zip(high_rated, vecs):
            weight = r["rating"] - 1  # ★2→1回、★3→2回
            rated_vecs.extend([vec] * weight)

    # interest_profileのEmbedding: ratings不足時のフォールバックスコアに使用
    # config.jsonのinterest_profile（自然言語7項目）をベクトル化
    profile_texts: list[str] = config["interest_profile"]
    profile_vecs: list[np.ndarray] = list(
        model.encode(profile_texts, show_progress_bar=False)
    )

    # α = ratings件数に応じた重み（0件=profile only、50件以上=instance only）
    alpha = compute_alpha(len(high_rated))
    print(f"[INFO] alpha={alpha:.2f} (ratings={len(high_rated)})")

    # 全クラスタをfinal_scoreでランキングし、上位top_clustersを選ぶ
    # final = α * cos_sim(centroid, rated_vecs平均) + (1-α) * cos_sim(centroid, profile_vecs平均)
    clusters = map_data["clusters"]
    ranked = rank_clusters(clusters, rated_vecs, profile_vecs, alpha)
    top = ranked[:top_clusters]

    print(f"[INFO] Top {top_clusters} clusters: {[c['label'] for c in top]}")

    # 上位クラスタ内の論文をarXiv APIで取得し、centroidとのcos類似度でスコアリング
    # match_score = cos_sim(クラスタcentroid, 論文embedding) → クラスタ中心に近い論文ほど高スコア
    recommendations = []
    for cluster in top:
        papers = fetch_papers_for_cluster(cluster["paper_ids"])
        if not papers:
            continue
        abstracts = [p.summary for p in papers]
        paper_vecs: list[np.ndarray] = list(
            model.encode(abstracts, show_progress_bar=False)
        )
        centroid = np.array(cluster["centroid"])

        for paper, vec in zip(papers, paper_vecs):
            match_score = _cosine_similarity(centroid, vec)
            arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
            recommendations.append(
                {
                    "id": arxiv_id,
                    "title": paper.title,
                    "abstract": paper.summary,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "match_score": round(match_score, 4),
                    "matched_cluster": cluster["label"],
                    "submitted": paper.published.strftime("%Y-%m-%d"),
                }
            )

    # min_match_score未満を除外し、スコア降順で上位top_nに絞る
    min_match: float = rec_config["min_match_score"]
    recommendations = [r for r in recommendations if r["match_score"] >= min_match]
    recommendations.sort(key=lambda r: r["match_score"], reverse=True)
    recommendations = recommendations[:top_n]

    output: dict[str, Any] = {
        "generated_at": datetime.now(JST).isoformat(),
        "top_clusters": [{"label": c["label"], "score": c["score"]} for c in top],
        "recommendations": recommendations,
    }

    out_path = output_dir / "recommendations.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved {len(recommendations)} recommendations to {out_path}")

    # datamapplotでmap.htmlを再生成（top_clustersをオレンジでハイライト）
    html_path = ROOT / "public" / "map.html"
    if not map_data.get("papers"):
        print(
            "[INFO] Skipping map.html regeneration (papers data not found in map.json)"
        )
        return
    html_path.parent.mkdir(parents=True, exist_ok=True)

    import datamapplot

    top_labels = {c["label"] for c in top}
    papers = map_data["papers"]
    cluster_label_map = {c["id"]: c["label"] for c in map_data["clusters"]}

    coords = np.array([[p["umap_x"], p["umap_y"]] for p in papers])
    point_labels = np.array(
        [cluster_label_map.get(p["cluster_id"], "Unlabelled") for p in papers]
    )
    # top_clusterはオレンジ、それ以外は青、ノイズはグレー（label_color_mapで指定）
    all_labels = {c["label"] for c in map_data["clusters"]}
    label_color_map = {
        label: ("#f59e0b" if label in top_labels else "#3b82f6")
        for label in all_labels
    }

    plot = datamapplot.create_interactive_plot(
        coords,
        point_labels,
        hover_text=np.array([p["id"] for p in papers]),
        title="arXiv Paper Map",
        enable_search=True,
        noise_label="Unlabelled",
        label_color_map=label_color_map,
        inline_data=True,
    )
    plot.save(str(html_path))
    print(f"[INFO] Updated map.html with top_clusters highlighted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate recommendations from ratings and map"
    )
    parser.add_argument("--top-clusters", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()
    main(args.top_clusters, args.top_n)
