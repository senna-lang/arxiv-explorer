"""
scripts/specter2.py のユニットテスト

モデルロードはモックするため、GPU/ダウンロード不要。
テスト対象:
- Specter2Encoder.encode() が ndarray を返す
- adapter を切り替えて encode できる
- バッチ分割が正しく動く
"""

import sys
import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_mock_model(hidden_size: int = 8):
    """AutoAdapterModel のモックを生成する"""
    import torch

    def fake_forward(**kwargs):
        batch = kwargs["input_ids"].shape[0]
        seq = kwargs["input_ids"].shape[1]
        out = MagicMock()
        out.last_hidden_state = torch.zeros(batch, seq, hidden_size)
        return out

    model = MagicMock(side_effect=fake_forward)
    model.eval.return_value = model
    return model


def _make_mock_tokenizer():
    """AutoTokenizer のモックを生成する"""
    import torch

    def fake_call(texts, **kwargs):
        n = len(texts) if isinstance(texts, list) else 1
        return {
            "input_ids": torch.zeros(n, 16, dtype=torch.long),
            "attention_mask": torch.ones(n, 16, dtype=torch.long),
        }

    return MagicMock(side_effect=fake_call)


class TestSpecter2Encoder:
    def _make_encoder(self, model_name="allenai/specter2_base"):
        from specter2 import Specter2Encoder

        mock_model = _make_mock_model()
        mock_tok = _make_mock_tokenizer()

        with (
            patch("specter2.AutoTokenizer.from_pretrained", return_value=mock_tok),
            patch("specter2.AutoAdapterModel.from_pretrained", return_value=mock_model),
        ):
            enc = Specter2Encoder(model_name)

        return enc

    def test_encode_returns_ndarray(self):
        enc = self._make_encoder()
        vecs = enc.encode(["paper one", "paper two"], adapter="proximity")
        assert isinstance(vecs, np.ndarray)
        assert vecs.shape[0] == 2

    def test_encode_single_text(self):
        enc = self._make_encoder()
        vecs = enc.encode(["single paper"], adapter="adhoc_query")
        assert vecs.shape[0] == 1

    def test_adapter_switched_for_proximity(self):
        enc = self._make_encoder()
        enc.encode(["paper"], adapter="proximity")
        enc._model.set_active_adapters.assert_called_with("proximity")

    def test_adapter_switched_for_adhoc_query(self):
        enc = self._make_encoder()
        enc.encode(["query"], adapter="adhoc_query")
        enc._model.set_active_adapters.assert_called_with("adhoc_query")

    def test_batch_split(self):
        enc = self._make_encoder()
        texts = [f"paper {i}" for i in range(10)]
        vecs = enc.encode(texts, adapter="proximity", batch_size=3)
        assert vecs.shape[0] == 10

    def test_hidden_dim_preserved(self):
        enc = self._make_encoder()
        vecs = enc.encode(["paper"], adapter="proximity")
        assert vecs.ndim == 2  # (n, hidden_dim)
