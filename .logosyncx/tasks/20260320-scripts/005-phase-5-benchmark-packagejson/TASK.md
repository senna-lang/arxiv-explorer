---
id: t-1024c3
date: 2026-03-20T12:36:19.279242+09:00
title: 'Phase 5: benchmark更新 + package.json + 最終確認'
seq: 5
status: done
priority: medium
plan: 20260320-scripts
tags: []
assignee: ""
completed_at: 2026-03-20T22:01:42.143784+09:00
---

## What

benchmark.py のimport先更新、package.json のスクリプトコマンド更新、全体の動作確認。

## Why

Phase 2-4 で旧ファイルが削除されるため、それらに依存する benchmark.py と package.json の更新が必要。

## Scope

- `scripts/benchmark.py` — inline load_config → core.config, from map → from map_pipeline
- `package.json` — python scripts/X.py → python -m scripts.X に更新

OUT of scope: パイプラインロジックの変更

## Acceptance Criteria

- [ ] `python -m scripts.benchmark --only recommend` が動作する
- [ ] `npm run daily`, `npm run recommend`, `npm run map` が動作する
- [ ] `pytest scripts/tests/ -v` が全パス

## Checklist

- [ ] benchmark.py: inline JSONC parsing → `from core.config import load_config`
- [ ] benchmark.py: `from map import main` → `from map_pipeline import main`
- [ ] package.json: スクリプトコマンド更新
- [ ] 全テスト実行
- [ ] パイプライン動作確認
