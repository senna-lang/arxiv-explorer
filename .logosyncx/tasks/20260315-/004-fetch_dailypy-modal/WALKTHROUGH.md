## Key Specification

USE_MODAL=1 のとき Modal T4 GPU 上で embedding を実行し、未設定のときはローカル動作を維持する。

## What Was Done

`fetch_daily.py` の `from specter2 import Specter2Encoder` を `from modal_app import build_encoder` に置き換え、`enc = Specter2Encoder(model_name)` を `enc = build_encoder(model_name)` に変更した（2行の変更のみ）。

## How It Was Done

`modal_app.py` の `build_encoder()` が `USE_MODAL` 環境変数を見て切り替えるため、スクリプト側の変更は最小限。`ModalEncoder` は `Specter2Encoder` と同じ `encode(texts, adapter, batch_size)` インターフェースを持つため、既存のコードはそのまま動く。

## Gotchas & Lessons Learned

- `Specter2Encoder` を直接呼ぶ箇所は `main()` 内の1行のみ。他は `enc.encode()` の呼び出しだけなので変更不要
- Pyright の `reportMissingImports` は `scripts/` が Python path に含まれていないための誤検知

## Reusable Patterns

```python
# 環境変数で切り替え（fetch_daily / recommend / map 共通パターン）
from modal_app import build_encoder
enc = build_encoder(model_name)  # USE_MODAL=1 → T4 GPU, 未設定 → ローカル
vecs = enc.encode(texts, adapter="proximity")
```
