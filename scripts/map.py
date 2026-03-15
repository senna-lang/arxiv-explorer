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
import hashlib
import json
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import arxiv
import numpy as np
from bertopic import BERTopic
from specter2 import Specter2Encoder

JST = ZoneInfo("Asia/Tokyo")
ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.jsonc"


def load_config() -> dict[str, Any]:
    import re
    text = CONFIG_PATH.read_text(encoding="utf-8")
    text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"|//[^\n]*',
                  lambda m: m.group(0) if m.group(0).startswith('"') else "", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def fetch_arxiv_papers(categories: list[str], max_papers: int, cache_dir: Path) -> list[Any]:
    """arXiv APIで対象カテゴリの論文を取得する。結果は当日中キャッシュする。"""
    today = datetime.now(JST).strftime("%Y%m%d")
    key = hashlib.md5(f"{sorted(categories)}{max_papers}".encode()).hexdigest()[:8]
    cache_path = cache_dir / f"arxiv_{today}_{key}.pkl"

    if cache_path.exists():
        print(f"[INFO] Loading from cache: {cache_path.name}")
        with open(cache_path, "rb") as f:
            return pickle.load(f)

    client = arxiv.Client(page_size=500, num_retries=3)
    query = " OR ".join(f"cat:{c}" for c in categories)
    search = arxiv.Search(
        query=query,
        max_results=max_papers,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    results = list(client.results(search))

    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump(results, f)
    print(f"[INFO] Cached {len(results)} papers to {cache_path.name}")
    return results


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
    papers: list[dict[str, Any]],
    total_papers: int,
    model: str,
) -> dict[str, Any]:
    """
    map.jsonのルート構造を組み立てる。
    papersは論文単位のUMAP 2D座標とcluster_idを含む（datamapplot用）。
    """
    return {
        "generated_at": datetime.now(JST).isoformat(),
        "total_papers": total_papers,
        "model": model,
        "clusters": clusters,
        "papers": papers,
    }


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
    enc = Specter2Encoder(model_name)
    embeddings: np.ndarray = enc.encode(texts, adapter="proximity", batch_size=32)

    # BERTopic の KeyBERTInspired はキーワード抽出時に embedding_model.embed_documents()
    # を呼ぶため、Specter2Encoder をラップして BERTopic のインターフェースに適合させる
    class _Specter2Backend:
        def embed_documents(self, docs: list[str], verbose: bool = False) -> np.ndarray:
            return enc.encode(docs, adapter="proximity")

    print("[INFO] Running BERTopic...")
    from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
    from hdbscan import HDBSCAN
    from sklearn.decomposition import PCA
    from sklearn.feature_extraction.text import CountVectorizer

    # PCA→UMAP(2D)を1パイプラインに統一: クラスタリングと可視化で同じ空間を使う
    # 2D UMAPでHDBSCANすることで「地図上の近さ」と「クラスタの近さ」が一致する
    # KeyBERTInspiredは元の768次元embeddingsを使うため次元不一致は生じない
    from sklearn.pipeline import make_pipeline
    from umap import UMAP

    umap_model = make_pipeline(
        PCA(n_components=t["pca_components"], random_state=42),
        UMAP(n_components=2, n_neighbors=t["umap_n_neighbors"], random_state=42, metric="cosine"),
    )
    min_cs = max(t["hdbscan_min_cluster_size_floor"], max_papers // t["hdbscan_min_cluster_size_divisor"])
    hdbscan_model = HDBSCAN(
        min_cluster_size=min_cs, min_samples=t["hdbscan_min_samples"], metric="euclidean", prediction_data=True
    )
    # プランA: sklearn英語318語 + 論文特有汎用語でc-TF-IDFノイズを除去
    # min_df=3で希少語を除外、max_df=0.85で全クラスタ共通語を統計的に除外
    ACADEMIC_STOPWORDS = [
        "model",
        "models",
        "method",
        "approach",
        "propose",
        "proposed",
        "result",
        "results",
        "paper",
        "work",
        "task",
        "performance",
        "training",
        "dataset",
        "data",
        "experiment",
        "experiments",
        "demonstrate",
        "achieve",
        "achieved",
        "using",
        "based",
        "learning",
        "neural",
        "deep",
        "large",
        "new",
        "existing",
        "different",
        "various",
        "show",
        "present",
        "study",
        "prediction",
        "predictions",
        "framework",
        "frameworks",
        "tasks",
        "evaluation",
        "accuracy",
        "state",
        "systems",
        # LLM系汎用語
        "llm",
        "llms",
        "language model",
        "language models",
        "large language",
        # 論文メタ定型文
        "code available",
        "github",
        "anonymous",
        "preprint",
        "arxiv",
        "supplementary",
        "appendix",
        # 汎用比較・実験語
        "real world",
        "baselines",
        "baseline",
        "datasets",
        "generalize",
        # LaTeX記号・数式表記
        "varepsilon",
        "mathbb",
        "mathcal",
        "mathbf",
        "sqrt",
        "theta",
        "alpha",
        "beta",
        "lambda",
        "sigma",
        "tilde",
        "widetilde",
        "frac",
        "textbf",
        "mathrm",
    ]
    base_stopwords = list(CountVectorizer(stop_words="english").get_stop_words() or [])
    # ngram_range=(1,1): bigramはc-TF-IDFで十分な共起頻度が得られない。
    # 意味的な複合概念はKeyBERTInspiredが担う。
    vectorizer = CountVectorizer(
        stop_words=base_stopwords + ACADEMIC_STOPWORDS,
        ngram_range=(1, 1),
        min_df=t["vectorizer_min_df"],
    )
    representation_model = [
        KeyBERTInspired(nr_repr_docs=t["keybert_nr_repr_docs"], nr_candidate_words=t["keybert_nr_candidate_words"], top_n_words=t["keybert_top_n_words"]),
        MaximalMarginalRelevance(diversity=t["mmr_diversity"], top_n_words=t["keybert_top_n_words"]),
    ]
    topic_model = BERTopic(
        embedding_model=_Specter2Backend(),
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        representation_model=representation_model,
        calculate_probabilities=False,
        verbose=True,
    )

    topics, _ = topic_model.fit_transform(abstracts, embeddings)

    # fit済みのumap_modelで2D座標を取得（クラスタリングと同一空間）
    umap_2d: np.ndarray = umap_model.transform(embeddings)

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

    # 論文単位のUMAP座標とcluster_idを保存（datamapplot用）
    # ノイズ(-1)は cluster_id=None として保持
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
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved map to {out_path}")

    # datamapplotでインタラクティブ地図を生成
    print("[INFO] Generating map.html with datamapplot...")
    import datamapplot

    point_labels = np.array(
        [topic_to_label.get(topics[i], "Unlabelled") for i in range(len(paper_ids))]
    )
    hover_texts = np.array(paper_ids)

    plot = datamapplot.create_interactive_plot(
        umap_2d,
        point_labels,
        hover_text=hover_texts,
        title="arXiv Paper Map",
        enable_search=True,
        noise_label="Unlabelled",
        inline_data=True,
    )
    html_path = ROOT / "public" / "map.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    plot.save(str(html_path))
    print(f"[INFO] Saved map.html to {html_path}")

    cluster_sizes = [c["size"] for c in clusters]
    noise_count = len(results) - sum(cluster_sizes)
    elapsed = round(time.time() - started_at, 1)
    print(f"[INFO] clusters={len(clusters)}, noise={noise_count}({round(noise_count/len(results)*100,1)}%), elapsed={elapsed}s")

    if log:
        log_entry = {
            "ts": datetime.now(JST).isoformat(),
            "max_papers": max_papers,
            "fetched": len(results),
            "min_cluster_size": min_cs,
            "n_clusters": len(clusters),
            "noise": noise_count,
            "noise_pct": round(noise_count / len(results) * 100, 1),
            "cluster_size": {
                "min": min(cluster_sizes),
                "max": max(cluster_sizes),
                "mean": round(sum(cluster_sizes) / len(cluster_sizes), 1),
            },
            "elapsed_sec": elapsed,
            "model": model_name,
            "tuning": t,
        }
        log_path = output_dir / "map_runs.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Logged to {log_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate arXiv topic map")
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10000,
        help="Maximum number of papers to fetch (default: 10000)",
    )
    parser.add_argument("--log", action="store_true", help="Record benchmark metrics to map_runs.jsonl")
    args = parser.parse_args()
    main(args.max_papers, log=args.log)
