---
id: t-1408b5
date: 2026-03-20T12:34:59.597653+09:00
title: 'Phase 1: core/ 共通ユーティリティ抽出'
seq: 1
status: done
priority: high
plan: 20260320-scripts
tags: []
assignee: ""
completed_at: 2026-03-20T21:10:06.716482+09:00
---

## What

3スクリプト（fetch_daily, map, recommend）に重複している共通コードを `scripts/core/` パッケージとして抽出する。振る舞い変更なし。

## Why

重複コードの一元化が後続のパッケージ分割の前提条件。ここを先にやることで後続フェーズが安全に進められる。

## Scope

- `scripts/core/__init__.py` (新規)
- `scripts/core/config.py` (新規) — load_config(), ROOT, CONFIG_PATH, JST
- `scripts/core/similarity.py` (新規) — cosine_similarity(), mean_cosine_similarity()
- `scripts/core/ratings.py` (新規) — load_ratings()
- `scripts/core/io.py` (新規) — save_json(), append_jsonl()
- `scripts/core/arxiv_client.py` (新規) — strip_version(), build_category_query()
- `scripts/fetch_daily.py` — core からの import に置換
- `scripts/map.py` — core からの import に置換
- `scripts/recommend.py` — core からの import に置換
- `scripts/tests/test_core_config.py` (新規)
- `scripts/tests/test_core_similarity.py` (新規)
- `scripts/tests/test_core_ratings.py` (新規)

OUT of scope: パッケージ分割（Phase 2-4）

## Acceptance Criteria

- [ ] `scripts/core/` に5モジュールが存在する
- [ ] fetch_daily.py, map.py, recommend.py のローカル load_config() 等が削除され core からの import に置換
- [ ] `pytest scripts/tests/` が全パス
- [ ] core モジュール用の新規テストが存在する

## Checklist

- [ ] core/config.py 作成 — 3箇所の load_config() + 定数を統合
- [ ] core/similarity.py 作成 — _cosine_similarity() を公開API化
- [ ] core/ratings.py 作成 — fetch_daily.py の堅牢版を採用
- [ ] core/io.py 作成 — save_json(), append_jsonl()
- [ ] core/arxiv_client.py 作成
- [ ] 3スクリプトの重複コードを core import に置換
- [ ] core 用テスト作成 (Red → Green → Refactor)
- [ ] `pytest scripts/tests/` passes
