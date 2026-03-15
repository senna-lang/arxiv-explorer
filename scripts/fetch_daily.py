"""
arXiv最新論文をレーティングとinterest_profileのα-blendで日次収集するスクリプト

処理フロー:
1. arXiv APIで対象カテゴリの直近N日の論文を取得
2. 過去30日分のdata/YYYYMMDD.jsonにある paper_id を除外（重複除去）
3. interest_profile + ratings(α-blend) でスコアリング
4. 上位top_n件をdata/YYYYMMDD.jsonに保存

スコアリングロジック（recommend.py の α-blend を流用）:
  α = min(1.0, n_high_rated / 50)
  score = α × mean_cosine(abstract, rated_papers) + (1-α) × mean_cosine(abstract, interest_profile)

Usage:
  python scripts/fetch_daily.py [--date YYYYMMDD] [--log]
"""

import argparse
import json
import re
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import arxiv
import numpy as np
from specter2 import Specter2Encoder

JST = ZoneInfo("Asia/Tokyo")
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.jsonc"


def load_config() -> dict[str, Any]:
    """config.jsonc を読み込む（コメント・末尾カンマを除去してJSONパース）"""
    text = CONFIG_PATH.read_text(encoding="utf-8")
    text = re.sub(
        r'"[^"\\]*(?:\\.[^"\\]*)*"|//[^\n]*',
        lambda m: m.group(0) if m.group(0).startswith('"') else "",
        text,
    )
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def load_ratings(config: dict[str, Any]) -> list[dict[str, Any]]:
    """
    ratings_urlが設定されていればHTTP(Cloudflare KV)、なければdata/ratings.jsonから読み込む。
    取得できない場合は空リストを返す。
    """
    ratings_url: str = config.get("ratings_url", "")
    output_dir = ROOT / config["output_dir"]

    if ratings_url:
        try:
            with urllib.request.urlopen(ratings_url) as res:
                data = json.loads(res.read())
            return data.get("ratings", [])
        except Exception as e:
            print(f"[WARN] Failed to fetch ratings from {ratings_url}: {e}")

    ratings_path = output_dir / "ratings.json"
    if ratings_path.exists():
        with open(ratings_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("ratings", [])

    print("[WARN] No ratings source available. Using profile-only scoring.")
    return []


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


def fetch_recent_papers(
    config: dict[str, Any], max_candidates: int
) -> list[dict[str, Any]]:
    """
    arXiv APIで config.categories の各カテゴリから最新 max_candidates 件を取得する。
    日付フィルタは使わない（週末・祝日はarXivが更新しないため、固定日数だと0件になる）。
    重複除去は呼び出し元の deduplicate() に委ねる。
    """
    categories: list[str] = config["categories"]
    query = " OR ".join(f"cat:{c}" for c in categories)

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

        raw_id = result.entry_id.split("/")[-1]
        arxiv_id = re.sub(r"v\d+$", "", raw_id)

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


def deduplicate(
    papers: list[dict[str, Any]], seen_ids: set[str]
) -> list[dict[str, Any]]:
    """seen_ids に含まれる paper_id を除外して返す。"""
    return [p for p in papers if p["id"] not in seen_ids]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """2ベクトルのcos類似度を返す。ゼロベクトルは0.0として扱う。"""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def score_papers(
    papers: list[dict[str, Any]],
    vecs: np.ndarray,
    rated_vecs: list[np.ndarray],
    profile_vecs: list[np.ndarray],
    alpha: float,
    top_n: int,
) -> list[dict[str, Any]]:
    """
    各論文の埋め込みベクトルと rated_vecs / profile_vecs の cos 類似度から
    α-blend スコアを計算し、スコア降順で top_n 件を返す。

    score = α × mean_cosine(vec, rated_vecs) + (1-α) × mean_cosine(vec, profile_vecs)
    """
    scored: list[dict[str, Any]] = []
    for paper, vec in zip(papers, vecs):
        if rated_vecs:
            instance_score = float(
                np.mean([_cosine_similarity(vec, rv) for rv in rated_vecs])
            )
        else:
            instance_score = 0.0

        if profile_vecs:
            profile_score = float(
                np.mean([_cosine_similarity(vec, pv) for pv in profile_vecs])
            )
        else:
            profile_score = 0.0

        final_score = alpha * instance_score + (1 - alpha) * profile_score
        scored.append({**paper, "score": round(final_score, 4)})

    scored.sort(key=lambda p: p["score"], reverse=True)
    return scored[:top_n]


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

    enc = Specter2Encoder(model_name)

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
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

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
        log_path = output_dir / "fetch_daily_runs.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Logged to {log_path.name}")


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
