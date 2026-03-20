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
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import arxiv
import numpy as np
from modal_app import app, build_encoder

JST = ZoneInfo("Asia/Tokyo")
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.jsonc"


def load_config() -> dict[str, Any]:
    import re

    text = CONFIG_PATH.read_text(encoding="utf-8")
    text = re.sub(
        r'"[^"\\]*(?:\\.[^"\\]*)*"|//[^\n]*',
        lambda m: m.group(0) if m.group(0).startswith('"') else "",
        text,
    )
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


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


def compute_alpha(n_ratings: int, threshold: int) -> float:
    """
    ratings件数に応じたα値を返す。
    0件=0.0、threshold件以上=1.0、線形補間。
    """
    return min(1.0, n_ratings / threshold)


def compute_final_score(instance: float, profile: float, alpha: float) -> float:
    """
    instance_scoreとprofile_scoreをα加重合成する。
    final = α * instance + (1-α) * profile
    """
    return alpha * instance + (1 - alpha) * profile


def select_serendipity_papers(
    papers_with_scores: list[dict],
    min_score: float,
    max_score: float,
    top_n: int,
    exclude_ids: set[str],
    filter_key: str = "match_score",
) -> list[dict]:
    """
    filter_key のスコアバンド [min_score, max_score] で絞り込み、上位top_nを返す。
    exclude_ids に含まれるIDは除外する（recommendationsとの重複防止）。
    filter_key="centroid_score" を指定するとクラスタ内代表度でフィルタできる。
    """
    filtered = [
        p for p in papers_with_scores
        if min_score <= p[filter_key] <= max_score and p["id"] not in exclude_ids
    ]
    filtered.sort(key=lambda p: p[filter_key], reverse=True)
    return filtered[:top_n]


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

    enc = build_encoder(model_name)

    # 高評価論文のEmbedding: proximity アダプタ（論文↔論文類似度）
    rated_vecs: list[np.ndarray] = []
    if high_rated:
        texts = [f"{r.get('title', '')} [SEP] {r['abstract']}" for r in high_rated]
        vecs = list(enc.encode(texts, adapter="proximity"))
        for r, vec in zip(high_rated, vecs):
            weight = r["rating"] - 1  # ★2→1回、★3→2回
            rated_vecs.extend([vec] * weight)

    # interest_profileのEmbedding: adhoc_query アダプタ（クエリ→論文検索）
    profile_texts: list[str] = config["interest_profile"]
    profile_vecs: list[np.ndarray] = list(
        enc.encode(profile_texts, adapter="adhoc_query")
    )

    # α = ratings件数に応じた重み（0件=profile only、50件以上=instance only）
    alpha = compute_alpha(len(high_rated), t["alpha_ratings_threshold"])
    print(f"[INFO] alpha={alpha:.2f} (ratings={len(high_rated)})")

    # 全クラスタをfinal_scoreでランキングし、上位top_clustersを選ぶ
    # final = α * cos_sim(centroid, rated_vecs平均) + (1-α) * cos_sim(centroid, profile_vecs平均)
    clusters = map_data["clusters"]
    ranked = rank_clusters(clusters, rated_vecs, profile_vecs, alpha)
    top = ranked[:top_clusters]

    # セレンディピティ: 隣接クラスタ（rank 4〜）と意図的に遠いクラスタ（末尾から）を取得
    ser_n_clusters: int = rec_config.get("serendipity_clusters", 3)
    ser_distant_n: int = rec_config.get("serendipity_distant_clusters", 2)
    ser_top = ranked[top_clusters : top_clusters + ser_n_clusters]
    ser_distant = ranked[max(top_clusters + ser_n_clusters, len(ranked) - ser_distant_n) :]

    print(f"[INFO] Top {top_clusters} clusters: {[c['label'] for c in top]}")
    print(f"[INFO] Serendipity adjacent clusters: {[c['label'] for c in ser_top]}")
    print(f"[INFO] Serendipity distant clusters: {[c['label'] for c in ser_distant]}")

    # 上位クラスタ内の論文をarXiv APIで取得し、α-blendスコアでスコアリング
    # match_score = α × cos_sim(論文, 高評価論文) + (1-α) × cos_sim(論文, interest_profile)
    recommendations = []
    for cluster in top:
        papers = fetch_papers_for_cluster(cluster["paper_ids"])
        if not papers:
            continue
        texts = [f"{p.title} [SEP] {p.summary}" for p in papers]
        paper_vecs: list[np.ndarray] = list(
            enc.encode(texts, adapter="proximity")
        )
        centroid = np.array(cluster["centroid"])

        for paper, vec in zip(papers, paper_vecs):
            centroid_score = _cosine_similarity(centroid, vec)
            instance = compute_instance_score(vec, rated_vecs)
            profile = compute_instance_score(vec, profile_vecs)
            match_score = compute_final_score(instance, profile, alpha)
            arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
            recommendations.append(
                {
                    "id": arxiv_id,
                    "title": paper.title,
                    "abstract": paper.summary,
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "match_score": round(match_score, 4),
                    "centroid_score": round(centroid_score, 4),
                    "matched_cluster": cluster["label"],
                    "submitted": paper.published.strftime("%Y-%m-%d"),
                }
            )

    # centroid_score で代表論文を絞り込み（クラスタ内の質担保）、match_score降順で上位top_nに絞る
    min_match: float = rec_config["min_match_score"]
    recommendations = [r for r in recommendations if r["centroid_score"] >= min_match]
    recommendations.sort(key=lambda r: r["match_score"], reverse=True)
    recommendations = recommendations[:top_n]

    # セレンディピティ論文: 隣接クラスタ代表論文 + 遠いクラスタ代表論文を混在させる
    ser_min_match: float = rec_config.get("serendipity_min_match_score", 0.80)
    ser_top_n: int = rec_config.get("serendipity_top_n", 7)
    ser_distant_top_n: int = rec_config.get("serendipity_distant_top_n", 3)
    rec_ids = {r["id"] for r in recommendations}

    def _fetch_cluster_candidates(clusters: list[dict]) -> list[dict]:
        """クラスタ内論文を取得し、α-blendスコア（ユーザーの興味との類似度）を計算する。
        match_score = α × cos_sim(論文, 高評価論文平均) + (1-α) × cos_sim(論文, interest_profile平均)
        クラスタ内代表度ではなくユーザー関連度を表すため、セレンディピティでも意味ある数値になる。
        """
        candidates: list[dict] = []
        for cluster in clusters:
            papers = fetch_papers_for_cluster(cluster["paper_ids"])
            if not papers:
                continue
            texts = [f"{p.title} [SEP] {p.summary}" for p in papers]
            vecs: list[np.ndarray] = list(enc.encode(texts, adapter="proximity"))
            centroid = np.array(cluster["centroid"])
            for paper, vec in zip(papers, vecs):
                centroid_score = _cosine_similarity(centroid, vec)
                # α-blend: ユーザーの興味（rated_vecs/profile_vecs）との類似度
                instance = compute_instance_score(vec, rated_vecs)
                profile = compute_instance_score(vec, profile_vecs)
                user_score = compute_final_score(instance, profile, alpha)
                arxiv_id = paper.entry_id.split("/")[-1].split("v")[0]
                candidates.append(
                    {
                        "id": arxiv_id,
                        "title": paper.title,
                        "abstract": paper.summary,
                        "url": f"https://arxiv.org/abs/{arxiv_id}",
                        "match_score": round(user_score, 4),
                        "centroid_score": round(centroid_score, 4),
                        "matched_cluster": cluster["label"],
                        "submitted": paper.published.strftime("%Y-%m-%d"),
                    }
                )
        return candidates

    adjacent = select_serendipity_papers(
        _fetch_cluster_candidates(ser_top),
        min_score=ser_min_match, max_score=1.0,
        top_n=ser_top_n, exclude_ids=rec_ids,
        filter_key="centroid_score",
    )
    distant_exclude = rec_ids | {p["id"] for p in adjacent}
    distant = select_serendipity_papers(
        _fetch_cluster_candidates(ser_distant),
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
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

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
                "mean": round(sum(match_scores) / len(match_scores), 4)
                if match_scores
                else None,
            },
            "elapsed_sec": round(time.time() - started_at, 1),
            "model": model_name,
            "tuning": {
                **t,
                "min_rating": min_rating,
                "top_clusters": top_clusters,
                "top_n": top_n,
                "min_match_score": rec_config["min_match_score"],
            },
        }
        log_path = output_dir / "recommend_runs.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Logged to {log_path.name}")

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
    ser_labels = {c["label"] for c in ser_top}
    papers = map_data["papers"]
    cluster_label_map = {c["id"]: c["label"] for c in map_data["clusters"]}

    coords = np.array([[p["umap_x"], p["umap_y"]] for p in papers])
    point_labels = np.array(
        [cluster_label_map.get(p["cluster_id"], "Unlabelled") for p in papers]
    )
    # top_clusterはオレンジ、セレンディピティは緑、それ以外は青
    all_labels = {c["label"] for c in map_data["clusters"]}
    label_color_map = {
        label: (
            "#f59e0b" if label in top_labels
            else "#10b981" if label in ser_labels
            else "#3b82f6"
        )
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
    print("[INFO] Updated map.html with top_clusters highlighted")


@app.local_entrypoint()
def modal_main(top_clusters: int = 3, top_n: int = 20, log: bool = False) -> None:
    """modal run scripts/recommend.py 用エントリポイント。"""
    main(top_clusters, top_n, log=log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate recommendations from ratings and map"
    )
    parser.add_argument("--top-clusters", type=int, default=3)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument(
        "--log",
        action="store_true",
        help="Record benchmark metrics to recommend_runs.jsonl",
    )
    args = parser.parse_args()
    main(args.top_clusters, args.top_n, log=args.log)
