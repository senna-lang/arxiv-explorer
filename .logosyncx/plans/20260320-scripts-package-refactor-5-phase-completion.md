---
id: c6cc1f
topic: scripts package refactor 5-phase completion
tags:
    - python
agent: claude-sonnet-4-6
related: []
tasks_dir: .logosyncx/tasks/20260320-scripts-package-refactor-5-phase-completion
distilled: false
---

## Background

`scripts/` 配下の Python スクリプト（fetch_daily.py: 335行, map.py: 427行, recommend.py: 409行）がモノリシック構造で、共通コードが3箇所に重複していた。単一責任・テスタブル性を意識した構造にリアーキした。

## Spec

全5フェーズで完了:

- **Phase 1**: `scripts/core/` 共通ユーティリティ抽出（config, similarity, ratings, io, arxiv_client）
- **Phase 2**: `scripts/fetch_daily/` パッケージ化（cli, fetch, dedup, scoring）
- **Phase 3**: `scripts/map_pipeline/` パッケージ化（cli, fetch, clustering, aggregation, visualization）
- **Phase 4**: `scripts/recommend/` パッケージ化（cli, cluster_ranking, serendipity, visualization）
- **Phase 5**: benchmark.py + package.json 更新

## Key Decisions

- Decision: `core/` を先に作る（Phase 1）。Rationale: 後続フェーズが安全に進められる前提条件。
- Decision: 各パッケージの `__init__.py` で後方互換 re-export。Rationale: test_*.py や benchmark.py の import を最小限の変更で済ます。
- Decision: `Path(__file__).resolve()` で絶対パス化。Rationale: pytest 実行時に相対パスになるケースがあり ROOT が狂う。
- Decision: Modal duplicate entrypoint 問題は放置。Rationale: pytest をグループ別実行で回避できる既知問題。

## Notes

- テスト総数: 106ケース（全パス）
- 削除したファイル: fetch_daily.py, map.py, recommend.py, test_recommend.py（迷子）
- package.json は `python scripts/X.py` → `python -m scripts.X` に統一
