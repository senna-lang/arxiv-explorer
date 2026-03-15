"""
SPECTER2 アダプタ付きエンコーダ

用途別アダプタを切り替えて論文テキストを埋め込む。
- proximity    : 論文↔論文の類似度（fetch_daily, recommend）
- adhoc_query  : クエリ→論文の検索（interest_profile スコアリング）

Usage:
    enc = Specter2Encoder("allenai/specter2_base")
    paper_vecs   = enc.encode(paper_texts,   adapter="proximity")
    profile_vecs = enc.encode(profile_texts, adapter="adhoc_query")
"""

from typing import Literal

import numpy as np
from adapters import AutoAdapterModel
from transformers import AutoTokenizer

AdapterType = Literal["proximity", "adhoc_query"]

_ADAPTER_IDS: dict[str, str] = {
    "proximity": "allenai/specter2",
    "adhoc_query": "allenai/specter2_adhoc_query",
}


class Specter2Encoder:
    """
    SPECTER2 base + アダプタを保持し、encode() でベクトルを返すエンコーダ。

    モデルとアダプタは初期化時に一度だけロードする。
    encode() ごとに set_active_adapters() でアダプタを切り替える。
    """

    def __init__(self, model_name: str) -> None:
        self._tokenizer = AutoTokenizer.from_pretrained(model_name)
        self._model = AutoAdapterModel.from_pretrained(model_name)

        # 両アダプタをあらかじめロード
        for name, adapter_id in _ADAPTER_IDS.items():
            self._model.load_adapter(adapter_id, source="hf", load_as=name)

        self._model.eval()
        # eval() 後にデフォルトアダプタを設定（警告抑制）
        self._model.set_active_adapters("proximity")

    def encode(
        self,
        texts: list[str],
        adapter: AdapterType,
        batch_size: int = 16,
    ) -> np.ndarray:
        """
        texts を指定アダプタで埋め込み、shape (len(texts), hidden_dim) の ndarray を返す。
        CLS トークンのベクトルを使用（SPECTER2 公式と同じ）。
        """
        import torch

        self._model.set_active_adapters(adapter)

        all_vecs: list[np.ndarray] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            inputs = self._tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
                return_token_type_ids=False,
            )
            with torch.no_grad():
                output = self._model(**inputs)
            # CLS トークン（index 0）を論文表現として使用
            vecs = output.last_hidden_state[:, 0, :].numpy()
            all_vecs.append(vecs)

        return np.vstack(all_vecs)
