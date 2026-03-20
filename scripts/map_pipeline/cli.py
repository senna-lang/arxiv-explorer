"""
map_pipeline CLI エントリポイント

arXiv論文群をBERTopicでクラスタリングしてarXiv地図（map.json）を生成する。

処理フロー:
1. arXiv APIで対象カテゴリの過去N件を取得
2. abstractをallenai/specter2でEmbedding
3. BERTopicでトピック抽出（UMAP random_state=42、HDBSCAN、c-TF-IDF）
4. 各クラスタのcentroid・UMAP 2D座標・キーワードを集約
5. data/map.jsonに保存

Usage:
  python -m scripts.map_pipeline [--max-papers N] [--log]
"""

import argparse
import time
from datetime import datetime
from typing import Any

import numpy as np
from modal_app import app, build_encoder

from core.config import JST, ROOT, load_config
from core.io import append_jsonl, save_json

from .aggregation import build_cluster_dict, build_map_output
from .clustering import build_bertopic_model
from .fetch import fetch_arxiv_papers
from .visualization import generate_map_html


def main(max_papers: int, log: bool = False) -> None:
    config = load_config()
    output_dir = ROOT / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    model_name: str = config["embedding_model"]
    categories: list[str] = config["categories"]
    t: dict = config["tuning"]["map"]

    started_at = time.time()
    cache_dir = ROOT / ".cache"
    print(f"[INFO] Fetching up to {max_papers} papers from arXiv...")
    results = fetch_arxiv_papers(categories, max_papers, cache_dir)
    if not results:
        print("[ERROR] No papers fetched")
        return
    print(f"[INFO] Fetched {len(results)} papers")

    abstracts = [r.summary for r in results]
    paper_ids = [r.entry_id.split("/")[-1].split("v")[0] for r in results]
    texts = [f"{r.title} [SEP] {r.summary}" for r in results]

    print(f"[INFO] Embedding with {model_name}...")
    enc = build_encoder(model_name)
    embeddings: np.ndarray = enc.encode(texts, adapter="proximity", batch_size=32)

    print("[INFO] Running BERTopic...")
    topic_model = build_bertopic_model(enc, t, max_papers)
    topics, _ = topic_model.fit_transform(abstracts, embeddings)

    # fit済みの umap_model で 2D 座標を取得（クラスタリングと同一空間）
    umap_2d: np.ndarray = topic_model.umap_model.transform(embeddings)

    # クラスタごとに集約
    clusters: list[dict[str, Any]] = []
    unique_topics = sorted(set(topics))

    for topic_id in unique_topics:
        if topic_id == -1:
            continue  # ノイズクラスタはスキップ

        mask = [tp == topic_id for tp in topics]
        topic_paper_ids = [pid for pid, m in zip(paper_ids, mask) if m]
        topic_embeddings = embeddings[[i for i, m in enumerate(mask) if m]]
        topic_umap_2d = umap_2d[[i for i, m in enumerate(mask) if m]]

        centroid = topic_embeddings.mean(axis=0).tolist()
        umap_center = topic_umap_2d.mean(axis=0)

        topic_words = topic_model.get_topic(topic_id)
        keywords = [word for word, _ in topic_words[:10]] if topic_words else []

        clusters.append(
            build_cluster_dict(
                topic_id=topic_id,
                keywords=keywords,
                centroid=centroid,
                paper_ids=topic_paper_ids,
                umap_x=float(umap_center[0]),
                umap_y=float(umap_center[1]),
            )
        )

    print(f"[INFO] Found {len(clusters)} clusters")

    # 論文単位の UMAP 座標と cluster_id を保存（datamapplot 用）
    topic_to_label = {c["id"]: c["label"] for c in clusters}
    papers_list: list[dict[str, Any]] = [
        {
            "id": pid,
            "umap_x": round(float(umap_2d[i, 0]), 4),
            "umap_y": round(float(umap_2d[i, 1]), 4),
            "cluster_id": topics[i] if topics[i] != -1 else None,
        }
        for i, pid in enumerate(paper_ids)
    ]

    output = build_map_output(
        clusters=clusters,
        papers=papers_list,
        total_papers=len(results),
        model=model_name,
    )

    out_path = output_dir / "map.json"
    save_json(out_path, output)
    print(f"[INFO] Saved map to {out_path}")

    # datamapplot でインタラクティブ地図を生成
    print("[INFO] Generating map.html with datamapplot...")
    html_path = ROOT / "public" / "map.html"
    generate_map_html(umap_2d, paper_ids, topic_to_label, topics, html_path)

    cluster_sizes = [c["size"] for c in clusters]
    noise_count = len(results) - sum(cluster_sizes)
    elapsed = round(time.time() - started_at, 1)
    print(
        f"[INFO] clusters={len(clusters)}, noise={noise_count}"
        f"({round(noise_count/len(results)*100,1)}%), elapsed={elapsed}s"
    )

    if log:
        log_entry = {
            "ts": datetime.now(JST).isoformat(),
            "max_papers": max_papers,
            "fetched": len(results),
            "min_cluster_size": max(
                t["hdbscan_min_cluster_size_floor"],
                max_papers // t["hdbscan_min_cluster_size_divisor"],
            ),
            "n_clusters": len(clusters),
            "noise": noise_count,
            "noise_pct": round(noise_count / len(results) * 100, 1),
            "cluster_size": {
                "min": min(cluster_sizes),
                "max": max(cluster_sizes),
                "mean": round(sum(cluster_sizes) / len(cluster_sizes), 1),
            },
            "cluster_labels": [c["label"] for c in clusters],
            "elapsed_sec": elapsed,
            "model": model_name,
            "tuning": t,
        }
        append_jsonl(output_dir / "map_runs.jsonl", log_entry)
        print("[INFO] Logged to map_runs.jsonl")


@app.local_entrypoint()
def modal_main(max_papers: int = 10000, log: bool = False) -> None:
    """modal run scripts/map_pipeline/ 用エントリポイント。"""
    main(max_papers, log=log)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate arXiv topic map")
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10000,
        help="Maximum number of papers to fetch (default: 10000)",
    )
    parser.add_argument(
        "--log", action="store_true", help="Record benchmark metrics to map_runs.jsonl"
    )
    args = parser.parse_args()
    main(args.max_papers, log=args.log)
