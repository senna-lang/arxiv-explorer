---
id: t-0b7c2b
date: 2026-03-17T22:17:11.499293+09:00
title: modal_app.py 作成（GPU image・Volume定義）
seq: 3
status: done
priority: high
plan: 20260315-
tags: []
assignee: ""
completed_at: 2026-03-17T23:02:29.684057+09:00
---

## What

Modal の共通設定（App・GPU image・Volume）を定義する `scripts/modal_app.py` を作成する。fetch_daily / recommend / map の各スクリプトがここから image と volume を import して使う。

## Why

GPU image と specter2_base のモデルキャッシュ Volume を一箇所で定義することで、3スクリプト間で設定を共有し重複を避ける。

## Scope

- `scripts/modal_app.py`（新規作成）

OUT of scope: 各スクリプトの Modal 対応（タスク 4〜6）

## Acceptance Criteria

- [ ] `modal_app.py` が存在する
- [ ] `modal app` として T4 GPU image が定義されている
- [ ] `modal.Volume` でモデルキャッシュが定義されている
- [ ] `modal deploy scripts/modal_app.py` がエラーなく通る

## Checklist

- [ ] `modal.App` 定義
- [ ] GPU image: `modal.Image.debian_slim().pip_install(...)` + CUDA 対応 torch
- [ ] `modal.Volume` でキャッシュパス（`/root/.cache/huggingface`）を永続化
- [ ] `modal deploy` で疎通確認

## Notes

```python
import modal

app = modal.App("arxiv-newspaper")

image = (
    modal.Image.debian_slim()
    .pip_install("torch", extra_index_url="https://download.pytorch.org/whl/cu118")
    .pip_install("sentence-transformers", "arxiv", "numpy", ...)
)

model_volume = modal.Volume.from_name("arxiv-model-cache", create_if_missing=True)
MODEL_CACHE_PATH = "/root/.cache/huggingface"
```

GPU 指定は各 `@modal.function` で `gpu="T4"` を付ける。
