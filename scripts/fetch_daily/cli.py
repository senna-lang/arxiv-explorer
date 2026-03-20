"""
fetch_daily CLI エントリポイント

arXiv最新論文をレーティングとinterest_profileのα-blendで日次収集する。

処理フロー:
1. arXiv APIで対象カテゴリの直近N日の論文を取得
2. 過去30日分のdata/YYYYMMDD.jsonにある paper_id を除外（重複除去）
3. interest_profile + ratings(α-blend) でスコアリング
4. 上位top_n件をdata/YYYYMMDD.jsonに保存

Usage:
  python -m scripts.fetch_daily [--date YYYYMMDD] [--log]
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

from .dedup import deduplicate, load_seen_ids
from .fetch import fetch_recent_papers
from .scoring import score_papers


def main(date_str: str, log: bool = False) -> None:
    config = load_config()
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    fetch_cfg: dict[str, Any] = config.get("fetch_daily", {})
    max_candidates: int = fetch_cfg.get("max_candidates", 300)
    top_n: int = fetch_cfg.get("top_n", 20)
    dedupe_days: int = fetch_cfg.get("dedupe_days", 30)
    min_rating: int = config.get("recommendation", {}).get("min_rating", 2)
    alpha_threshold: int = (
        config.get("tuning", {}).get("recommend", {}).get("alpha_ratings_threshold", 50)
    )
    model_name: str = config["embedding_model"]

    started_at = time.time()

    print(f"[INFO] Fetching recent papers (max_candidates={max_candidates})")
    candidates = fetch_recent_papers(config, max_candidates)
    print(f"[INFO] Fetched {len(candidates)} candidates from arXiv")

    seen_ids = load_seen_ids(output_dir, days=dedupe_days)
    candidates = deduplicate(candidates, seen_ids)
    print(f"[INFO] {len(candidates)} candidates after deduplication")

    if not candidates:
        print("[WARN] No new candidates to score. Exiting.")
        return

    ratings = load_ratings(config)
    high_rated = [r for r in ratings if r.get("rating", 0) >= min_rating]
    print(f"[INFO] {len(high_rated)} high-rated papers (rating>={min_rating})")

    enc = build_encoder(model_name)

    # 論文テキスト: proximity アダプタ（論文↔論文の類似度に最適）
    print(f"[INFO] Embedding {len(candidates)} candidate papers (proximity adapter)...")
    texts = [f"{p['title']} [SEP] {p['abstract']}" for p in candidates]
    vecs: np.ndarray = enc.encode(texts, adapter="proximity")

    # 高評価論文のEmbedding: ★3は★2の2倍の重みで rated_vecs に追加（proximity）
    rated_vecs: list[np.ndarray] = []
    if high_rated:
        rated_texts = [
            f"{r.get('title', '')} [SEP] {r['abstract']}" for r in high_rated
        ]
        raw_vecs = enc.encode(rated_texts, adapter="proximity")
        for r, vec in zip(high_rated, raw_vecs):
            weight = r["rating"] - 1  # ★2→1回、★3→2回
            rated_vecs.extend([vec] * weight)

    # interest_profile: adhoc_query アダプタ（クエリ→論文の検索に最適）
    profile_texts: list[str] = config["interest_profile"]
    print("[INFO] Embedding interest profile (adhoc_query adapter)...")
    profile_vecs: list[np.ndarray] = list(enc.encode(profile_texts, adapter="adhoc_query"))

    alpha = min(1.0, len(high_rated) / alpha_threshold)
    print(f"[INFO] alpha={alpha:.2f} (n_high_rated={len(high_rated)})")

    papers = score_papers(candidates, vecs, rated_vecs, profile_vecs, alpha, top_n)

    date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    output: dict[str, Any] = {
        "date": date_formatted,
        "collected_at": datetime.now(JST).isoformat(),
        "papers": papers,
        "meta": {
            "total": len(papers),
            "model": model_name,
            "source": "fetch_daily",
            "n_candidates": len(candidates),
            "n_ratings": len(high_rated),
            "alpha": round(alpha, 4),
        },
    }

    out_path = output_dir / f"{date_str}.json"
    save_json(out_path, output)
    print(f"[INFO] Saved {len(papers)} papers to {out_path}")

    if log:
        scores = [p["score"] for p in papers]
        log_entry = {
            "ts": datetime.now(JST).isoformat(),
            "date": date_formatted,
            "n_candidates": len(candidates),
            "n_ratings": len(high_rated),
            "alpha": round(alpha, 4),
            "n_papers": len(papers),
            "score": {
                "min": round(min(scores), 4) if scores else None,
                "max": round(max(scores), 4) if scores else None,
                "mean": round(sum(scores) / len(scores), 4) if scores else None,
            },
            "top_paper": papers[0]["title"] if papers else None,
            "elapsed_sec": round(time.time() - started_at, 1),
            "model": model_name,
        }
        append_jsonl(output_dir / "fetch_daily_runs.jsonl", log_entry)
        print(f"[INFO] Logged to fetch_daily_runs.jsonl")


@app.local_entrypoint()
def modal_main(date: str = "", log: bool = False) -> None:
    """modal run scripts/fetch_daily/ [--date YYYYMMDD] [--log] 用エントリポイント。"""
    date_str = date or datetime.now(JST).strftime("%Y%m%d")
    main(date_str, log=log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch recent arXiv papers and score with α-blend of ratings and interest_profile"
    )
    parser.add_argument(
        "--date",
        default=datetime.now(JST).strftime("%Y%m%d"),
        help="Output date in YYYYMMDD format (default: today)",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Record benchmark metrics to fetch_daily_runs.jsonl",
    )
    args = parser.parse_args()
    main(args.date, log=args.log)
