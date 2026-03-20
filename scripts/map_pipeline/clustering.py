"""
BERTopic クラスタリングモデル構築

提供:
- ACADEMIC_STOPWORDS: 学術論文特有の汎用語リスト
- build_bertopic_model(enc, tuning): BERTopic モデルを構築して返す
"""

import re
from typing import Any

import numpy as np
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from hdbscan import HDBSCAN
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import make_pipeline
from umap import UMAP

ACADEMIC_STOPWORDS = [
    "model", "models", "method", "approach", "propose", "proposed",
    "result", "results", "paper", "work", "task", "performance",
    "training", "dataset", "data", "experiment", "experiments",
    "demonstrate", "achieve", "achieved", "using", "based",
    "learning", "neural", "deep", "large", "new", "existing",
    "different", "various", "show", "present", "study",
    "prediction", "predictions", "framework", "frameworks",
    "tasks", "evaluation", "accuracy", "state", "systems",
    # LLM系汎用語
    "llm", "llms", "language model", "language models", "large language",
    # 論文メタ定型文
    "code available", "github", "anonymous", "preprint", "arxiv",
    "supplementary", "appendix",
    # 汎用比較・実験語
    "real world", "baselines", "baseline", "datasets", "generalize",
    # LaTeX記号・数式表記
    "varepsilon", "mathbb", "mathcal", "mathbf", "sqrt",
    "theta", "alpha", "beta", "lambda", "sigma", "tilde",
    "widetilde", "frac", "textbf", "mathrm",
]


def build_bertopic_model(enc: Any, tuning: dict[str, Any], max_papers: int) -> BERTopic:
    """
    BERTopic モデルを構築して返す。
    enc は Specter2Encoder（encode() メソッドを持つ）。
    tuning は config.tuning.map の辞書。
    """
    import nltk
    nltk.download("wordnet", quiet=True)
    from nltk.stem import WordNetLemmatizer
    _lemmatizer = WordNetLemmatizer()

    def _lemmatize_tokenizer(text: str) -> list[str]:
        tokens = re.findall(r"[a-z]+", text.lower())
        return [_lemmatizer.lemmatize(t) for t in tokens]

    # KeyBERTInspired はキーワード抽出時に embedding_model.embed_documents() を呼ぶ
    class _Specter2Backend:
        def embed_documents(self, docs: list[str], verbose: bool = False) -> np.ndarray:
            return enc.encode(docs, adapter="proximity")

    t = tuning
    umap_model = make_pipeline(
        PCA(n_components=t["pca_components"], random_state=42),
        UMAP(
            n_components=2,
            n_neighbors=t["umap_n_neighbors"],
            random_state=42,
            metric="cosine",
        ),
    )
    min_cs = max(
        t["hdbscan_min_cluster_size_floor"],
        max_papers // t["hdbscan_min_cluster_size_divisor"],
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=min_cs,
        min_samples=t["hdbscan_min_samples"],
        metric="euclidean",
        prediction_data=True,
    )
    base_stopwords = list(CountVectorizer(stop_words="english").get_stop_words() or [])
    vectorizer = CountVectorizer(
        tokenizer=_lemmatize_tokenizer,
        stop_words=base_stopwords + ACADEMIC_STOPWORDS,
        ngram_range=(1, 1),
        min_df=t["vectorizer_min_df"],
    )
    representation_model = [
        KeyBERTInspired(
            nr_repr_docs=t["keybert_nr_repr_docs"],
            nr_candidate_words=t["keybert_nr_candidate_words"],
            top_n_words=t["keybert_top_n_words"],
        ),
        MaximalMarginalRelevance(
            diversity=t["mmr_diversity"],
            top_n_words=t["keybert_top_n_words"],
        ),
    ]
    return BERTopic(
        embedding_model=_Specter2Backend(),
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        representation_model=representation_model,
        calculate_probabilities=False,
        verbose=True,
    )
