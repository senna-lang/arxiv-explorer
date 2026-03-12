"""
arXiv論文群をBERTopicでクラスタリングしてarXiv地図（map.json）を生成する。

処理フロー:
1. arXiv APIで対象カテゴリの過去N件を取得
2. abstractをallenai/specter2でEmbedding
3. BERTopicでトピック抽出（UMAP random_state=42、HDBSCAN、c-TF-IDF）
4. 各クラスタのcentroid・UMAP 2D座標・キーワードを集約
5. data/map.jsonに保存

実行:
    python scripts/map.py
    python scripts/map.py --max-papers 20000
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import arxiv
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

JST = ZoneInfo("Asia/Tokyo")
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def fetch_arxiv_papers(categories: list[str], max_papers: int) -> list[Any]:
    """arXiv APIで対象カテゴリの論文を取得する。"""
    client = arxiv.Client(page_size=500, num_retries=3)
    query = " OR ".join(f"cat:{c}" for c in categories)
    search = arxiv.Search(
        query=query,
        max_results=max_papers,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    return list(client.results(search))


def generate_label(keywords: list[str]) -> str:
    """
    クラスタキーワードから人間可読なラベルを生成する。
    先頭3キーワードを ' & ' で結合する。
    """
    if not keywords:
        return "unknown"
    top = keywords[:3]
    return " & ".join(top)


def build_cluster_dict(
    topic_id: int,
    keywords: list[str],
    centroid: list[float],
    paper_ids: list[str],
    umap_x: float,
    umap_y: float,
) -> dict[str, Any]:
    """
    クラスタ情報をmap.jsonのスキーマに準拠したdictに変換する。
    """
    return {
        "id": topic_id,
        "keywords": keywords,
        "label": generate_label(keywords),
        "centroid": centroid,
        "paper_ids": paper_ids,
        "size": len(paper_ids),
        "umap_x": round(umap_x, 4),
        "umap_y": round(umap_y, 4),
    }


def build_map_output(
    clusters: list[dict[str, Any]],
    total_papers: int,
    model: str,
) -> dict[str, Any]:
    """
    map.jsonのルート構造を組み立てる。
    """
    return {
        "generated_at": datetime.now(JST).isoformat(),
        "total_papers": total_papers,
        "model": model,
        "clusters": clusters,
    }


def main(max_papers: int) -> None:
    config = load_config()
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    model_name: str = config["embedding_model"]
    categories: list[str] = config["categories"]

    print(f"[INFO] Fetching up to {max_papers} papers from arXiv...")
    results = fetch_arxiv_papers(categories, max_papers)
    if not results:
        print("[ERROR] No papers fetched")
        return
    print(f"[INFO] Fetched {len(results)} papers")

    abstracts = [r.summary for r in results]
    paper_ids = [r.entry_id.split("/")[-1].split("v")[0] for r in results]

    print(f"[INFO] Embedding with {model_name}...")
    model = SentenceTransformer(model_name)
    embeddings: np.ndarray = model.encode(abstracts, show_progress_bar=True)

    print("[INFO] Running BERTopic...")
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer

    # クラスタリング用: 高次元（10D）でHDBSCANに十分な密度情報を残す
    umap_cluster = UMAP(n_components=10, n_neighbors=15, random_state=42, metric="cosine")
    # 可視化用: 2DでUMAP座標を別途計算
    umap_viz = UMAP(n_components=2, n_neighbors=15, random_state=42, metric="cosine")
    # min_cluster_sizeはデータ件数に比例して調整（大規模ほど大きく）
    min_cs = max(20, max_papers // 200)
    hdbscan_model = HDBSCAN(min_cluster_size=min_cs, metric="euclidean", prediction_data=True)
    # stop_words="english" でthe/of/and等を除去、ngram_range=(1,2)で2単語フレーズも抽出
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2)
    topic_model = BERTopic(
        umap_model=umap_cluster,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        calculate_probabilities=False,
        verbose=True,
    )

    topics, _ = topic_model.fit_transform(abstracts, embeddings)

    # 可視化用に2D座標を別途計算
    print("[INFO] Computing 2D UMAP for visualization...")
    umap_2d = umap_viz.fit_transform(embeddings)

    # クラスタごとに集約
    clusters: list[dict[str, Any]] = []
    unique_topics = sorted(set(topics))

    for topic_id in unique_topics:
        if topic_id == -1:
            continue  # ノイズクラスタはスキップ

        mask = [t == topic_id for t in topics]
        topic_paper_ids = [pid for pid, m in zip(paper_ids, mask) if m]
        topic_embeddings = embeddings[[i for i, m in enumerate(mask) if m]]
        topic_umap_2d = umap_2d[[i for i, m in enumerate(mask) if m]]

        centroid = topic_embeddings.mean(axis=0).tolist()
        umap_center = topic_umap_2d.mean(axis=0)

        # BERTopicのキーワード取得
        topic_words = topic_model.get_topic(topic_id)
        keywords = [word for word, _ in topic_words[:10]] if topic_words else []

        clusters.append(build_cluster_dict(
            topic_id=topic_id,
            keywords=keywords,
            centroid=centroid,
            paper_ids=topic_paper_ids,
            umap_x=float(umap_center[0]),
            umap_y=float(umap_center[1]),
        ))

    print(f"[INFO] Found {len(clusters)} clusters")

    output = build_map_output(
        clusters=clusters,
        total_papers=len(results),
        model=model_name,
    )

    out_path = output_dir / "map.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved map to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate arXiv topic map")
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10000,
        help="Maximum number of papers to fetch (default: 10000)",
    )
    args = parser.parse_args()
    main(args.max_papers)
