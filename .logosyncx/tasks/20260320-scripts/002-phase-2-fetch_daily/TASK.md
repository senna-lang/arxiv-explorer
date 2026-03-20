---
id: t-8f7660
date: 2026-03-20T12:35:21.382609+09:00
title: 'Phase 2: fetch_daily パッケージ化'
seq: 2
status: done
priority: high
plan: 20260320-scripts
tags: []
assignee: ""
completed_at: 2026-03-20T21:15:34.920737+09:00
---

## What

`scripts/fetch_daily.py`（335行）を `scripts/fetch_daily/` パッケージに分割。fetch/dedup/scoring を独立モジュール化し、cli.py をオーケストレーション専用にする。

## Why

arXiv API呼び出し・重複排除・スコアリングが混在しており、個別にテスト・修正しづらい。

## Scope

- `scripts/fetch_daily.py` → 削除
- `scripts/fetch_daily/__init__.py` (新規) — main() re-export
- `scripts/fetch_daily/cli.py` (新規) — argparse + main() + modal_main
- `scripts/fetch_daily/fetch.py` (新規) — fetch_recent_papers()
- `scripts/fetch_daily/dedup.py` (新規) — load_seen_ids(), deduplicate()
- `scripts/fetch_daily/scoring.py` (新規) — score_papers()
- `scripts/tests/test_fetch_daily_dedup.py` (移行)
- `scripts/tests/test_fetch_daily_scoring.py` (移行)

OUT of scope: map, recommend のパッケージ化

## Acceptance Criteria

- [ ] `scripts/fetch_daily/` パッケージが存在し、旧 fetch_daily.py は削除
- [ ] `python -m scripts.fetch_daily --date YYYYMMDD` が動作する
- [ ] benchmark.py の `from fetch_daily import main` が動作する
- [ ] `pytest scripts/tests/` が全パス

## Checklist

- [ ] fetch_daily/ パッケージ作成（__init__, cli, fetch, dedup, scoring）
- [ ] 旧 fetch_daily.py の関数を適切なモジュールに配置
- [ ] cli.py に main() オーケストレーション（~50行）
- [ ] テスト移行（test_fetch_daily.py → dedup + scoring に分割）
- [ ] `pytest scripts/tests/` passes
