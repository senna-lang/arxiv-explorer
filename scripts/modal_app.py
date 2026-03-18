"""
Modal アプリ定義

GPU image・Volume・Specter2Modal クラスと build_encoder() ファクトリを定義する。
fetch_daily.py / recommend.py / map.py は build_encoder() を呼ぶだけでよい。

  USE_MODAL=1  → Modal T4 GPU 上の Specter2Modal を使用
  未設定       → ローカルの Specter2Encoder をそのまま使用（後方互換）

Usage:
    from modal_app import build_encoder
    enc = build_encoder(model_name)          # USE_MODAL で自動切替
    vecs = enc.encode(texts, adapter="proximity")
"""

import os

import modal
import numpy as np

app = modal.App("arxiv-newspaper")

# CUDA 対応 image（torch cu118 + specter2 依存）
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch",
        extra_index_url="https://download.pytorch.org/whl/cu118",
    )
    .pip_install(
        "adapters",
        "transformers",
        "numpy",
        "sentence-transformers",
    )
)

# specter2_base（440MB）と各アダプタを永続キャッシュ
model_volume = modal.Volume.from_name("arxiv-model-cache", create_if_missing=True)
MODEL_CACHE_PATH = "/root/.cache/huggingface"

MODEL_NAME = "allenai/specter2_base"

# specter2.py をコンテナの /root/ に配置する
specter2_mount = modal.Mount.from_local_file(
    local_path="scripts/specter2.py",
    remote_path="/root/specter2.py",
)


@app.cls(
    gpu="T4",
    image=image,
    volumes={MODEL_CACHE_PATH: model_volume},
    mounts=[specter2_mount],
    timeout=1800,
)
class Specter2Modal:
    """
    Modal T4 GPU 上で動く Specter2Encoder ラッパー。

    コンテナ起動時に一度だけモデルをロードし、encode() で推論する。
    戻り値は JSON シリアライズ可能な list[list[float]] で返す。
    """

    @modal.enter()
    def load_model(self) -> None:
        import sys

        sys.path.insert(0, "/root")  # specter2_mount が /root/specter2.py に配置される
        from specter2 import Specter2Encoder

        self.enc = Specter2Encoder(MODEL_NAME)
        print(f"[Modal] Model loaded on device: {self.enc._device}")

    @modal.method()
    def encode(
        self,
        texts: list[str],
        adapter: str,
        batch_size: int = 32,
    ) -> list[list[float]]:
        """
        texts を指定アダプタで埋め込み、list[list[float]] で返す。
        呼び出し元は np.array(result) で ndarray に変換する。
        """
        vecs = self.enc.encode(texts, adapter=adapter, batch_size=batch_size)  # type: ignore[arg-type]
        return vecs.tolist()


class ModalEncoder:
    """
    Specter2Encoder と同じ encode() インターフェースを持つ Modal ラッパー。
    USE_MODAL=1 のとき build_encoder() が返す。
    """

    def __init__(self) -> None:
        self._cls = Specter2Modal()

    def encode(self, texts: list[str], adapter: str, batch_size: int = 32) -> np.ndarray:
        result = self._cls.encode.remote(texts, adapter, batch_size)
        return np.array(result)


def build_encoder(model_name: str) -> "ModalEncoder | object":
    """
    USE_MODAL=1 のとき Modal T4 上の ModalEncoder を返す。
    未設定のときはローカルの Specter2Encoder を返す。
    どちらも encode(texts, adapter, batch_size) を持つ共通インターフェース。
    """
    if os.getenv("USE_MODAL"):
        return ModalEncoder()
    from specter2 import Specter2Encoder
    return Specter2Encoder(model_name)
