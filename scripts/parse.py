"""
trend.mdのarXivセクションをパースし、arXiv APIでabstractを取得、
sentence-transformersでスコアリングしてdata/YYYYMMDD.jsonを生成する。

処理フロー:
1. config.jsonのtrend_dirからYYYYMMDD-trend.mdを読み込む
2. ## 📄 arXiv 注目論文セクションのMarkdownテーブルをパース → arXiv IDリストを抽出
3. arXiv APIで各論文のtitle/abstract/authors/categories/submitted/URLを取得
4. abstractをsentence-transformersでEmbedding
5. interest_profileの各文章とcos類似度を計算し平均をscoreとして付与
6. scoreの降順でソートしてdata/YYYYMMDD.jsonに保存

実行:
    python scripts/parse.py
    python scripts/parse.py --date 2026-03-11
"""

import argparse
import json
import re
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


def parse_trend_section(text: str) -> list[str]:
    """
    trend.mdのテキストから ## 📄 arXiv 注目論文 セクションを抽出し、
    arXiv IDリストを返す。重複は除去する。
    """
    section_match = re.search(
        r"## 📄 arXiv 注目論文.*?(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not section_match:
        return []

    section = section_match.group(0)
    # テーブル行から2列目（arXiv ID）を抽出
    # 行形式: | [タイトル](URL) | arXiv_ID | ...
    ids: list[str] = []
    seen: set[str] = set()
    for line in section.splitlines():
        cols = [c.strip() for c in line.split("|")]
        # テーブル行は | col1 | col2 | ... → split後は ['', col1, col2, ..., '']
        if len(cols) < 4:
            continue
        candidate = cols[2]  # 2列目 = arXiv ID
        if re.match(r"^\d{4}\.\d{4,5}$", candidate) and candidate not in seen:
            ids.append(candidate)
            seen.add(candidate)
    return ids


def fetch_arxiv_papers(ids: list[str]) -> list[Any]:
    """arXiv APIで論文情報を取得する。"""
    if not ids:
        return []
    client = arxiv.Client(num_retries=5)
    search = arxiv.Search(id_list=ids)
    return list(client.results(search))


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def compute_score(abstract_vec: np.ndarray, profile_vecs: list[np.ndarray]) -> float:
    """
    abstractのEmbeddingベクトルと、interest_profileの各文章ベクトルとの
    cos類似度の平均を返す。値域: 0.0 〜 1.0。
    """
    if not profile_vecs:
        return 0.0
    sims = [_cosine_similarity(abstract_vec, pv) for pv in profile_vecs]
    return float(np.mean(sims))


def build_paper_dict(result: Any, score: float) -> dict[str, Any]:
    """
    arxiv.Resultオブジェクトと算出済みscoreからJSONスキーマ準拠のdictを返す。
    """
    # entry_id例: "https://arxiv.org/abs/2603.08659v1"
    raw_id = result.entry_id.split("/")[-1]
    arxiv_id = re.sub(r"v\d+$", "", raw_id)

    url = f"https://arxiv.org/abs/{arxiv_id}"

    # GitHub URLをabstractから簡易抽出（存在する場合）
    github_match = re.search(r"https?://github\.com/[^\s\)]+", result.summary)
    github_url = github_match.group(0) if github_match else None

    paper: dict[str, Any] = {
        "id": arxiv_id,
        "title": result.title,
        "authors": [a.name for a in result.authors],
        "abstract": result.summary,
        "url": url,
        "categories": result.categories,
        "submitted": result.published.strftime("%Y-%m-%d"),
        "score": round(score, 4),
    }
    if github_url:
        paper["github_url"] = github_url

    return paper


def main(date_str: str) -> None:
    config = load_config()
    trend_dir = Path(config["trend_dir"])
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    trend_file = trend_dir / f"{date_str}-trend.md"
    if not trend_file.exists():
        print(f"[ERROR] trend file not found: {trend_file}")
        return

    text = trend_file.read_text(encoding="utf-8")
    ids = parse_trend_section(text)
    if not ids:
        print(f"[WARN] No arXiv IDs found in {trend_file}")
        return

    print(f"[INFO] Found {len(ids)} papers in trend.md")

    model = SentenceTransformer(config["embedding_model"])

    print("[INFO] Fetching papers from arXiv API...")
    results = fetch_arxiv_papers(ids)
    if not results:
        print("[ERROR] No papers fetched from arXiv API")
        return

    print(f"[INFO] Embedding {len(results)} abstracts...")
    abstracts = [r.summary for r in results]
    abstract_vecs: list[np.ndarray] = list(model.encode(abstracts, show_progress_bar=False))

    profile_texts: list[str] = config["interest_profile"]
    print("[INFO] Embedding interest profile...")
    profile_vecs: list[np.ndarray] = list(model.encode(profile_texts, show_progress_bar=False))

    papers = []
    for result, abstract_vec in zip(results, abstract_vecs):
        score = compute_score(abstract_vec, profile_vecs)
        papers.append(build_paper_dict(result, score))

    papers.sort(key=lambda p: p["score"], reverse=True)

    output: dict[str, Any] = {
        "date": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
        "collected_at": datetime.now(JST).isoformat(),
        "papers": papers,
        "meta": {
            "total": len(papers),
            "model": config["embedding_model"],
            "profile_version": "1",
        },
    }

    out_path = output_dir / f"{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved {len(papers)} papers to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse trend.md and generate YYYYMMDD.json")
    parser.add_argument(
        "--date",
        default=datetime.now(JST).strftime("%Y%m%d"),
        help="Date in YYYYMMDD format (default: today)",
    )
    args = parser.parse_args()
    main(args.date)
