## Key Specification

Modal T4 GPU image と specter2_base のモデルキャッシュ Volume を一箇所で定義し、fetch_daily / recommend / map の 3 スクリプトから共有できるようにする。

## What Was Done

- `scripts/specter2.py` に device 対応を追加（CPU/CUDA 自動切替、inputs の `.to(device)`、`.cpu().numpy()`）
- `scripts/modal_app.py` を新規作成: App・image・Volume・`Specter2Modal` クラスを定義

## How It Was Done

**specter2.py の変更点**:
- `__init__` に `device` 引数追加（デフォルト: cuda があれば cuda、なければ cpu）
- `self._model.to(self._device)` でモデルをデバイスへ移動
- `encode()` 内で `inputs = {k: v.to(self._device) ...}` を追加
- `.numpy()` → `.cpu().numpy()` に変更（CUDA テンソルはそのまま .numpy() 不可）

**modal_app.py の設計**:
- `@app.cls(gpu="T4", ...)` + `@modal.enter()` でコンテナ起動時にモデルを一度だけロード
- Volume を `/root/.cache/huggingface` にマウントしてモデルキャッシュを永続化
- 戻り値は `list[list[float]]`（JSON シリアライズ可能）。呼び出し元で `np.array()` に変換する

## Gotchas & Lessons Learned

- `modal.parameter()` はバージョンによって API が異なるため使用せず、モデル名はモジュール定数で固定
- specter2.py の `sys.path.insert` が必要（Modal コンテナ内では scripts/ がパスに入っていないため）

## Reusable Patterns

```python
# 呼び出し側（fetch_daily など）
import numpy as np
from modal_app import Specter2Modal

encoder = Specter2Modal()
vecs = np.array(encoder.encode.remote(texts, adapter="proximity"))
```
