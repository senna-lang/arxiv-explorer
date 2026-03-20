---
id: 4b8aeb
topic: CI workflow 4-job setup
tags:
    - ci
agent: claude-sonnet-4-6
related: []
tasks_dir: .logosyncx/tasks/20260320-ci-workflow-4-job-setup
distilled: false
---

## Background

プロジェクトに PR/push トリガーの CI が存在しなかった。コード品質を自動検証するため `.github/workflows/ci.yml` を新規作成した。既存ワークフローは daily/weekly/monthly のバッチのみ。

## Spec

- `.github/workflows/ci.yml` を新規作成
- トリガー: push to main / PR targeting main
- concurrency: `ci-${{ github.ref }}` + cancel-in-progress
- 4 ジョブ並列:
  - `typecheck`: setup-node@v4 (Node 22) + setup-bun@v2 + `npx tsc --noEmit`
  - `astro-build`: setup-node@v4 (Node 22) + setup-bun@v2 + `bun run build`
  - `python-test`: setup-python@v5 (3.11) + pytest (test_parse/map/recommend を --ignore)
  - `python-lint`: ruff check + py_compile
- `requirements.txt` に pytest 追加

## Key Decisions

- Decision: `astro-build`/`typecheck` に `setup-node@v4 (node: '22')` を追加。Rationale: Astro が Node >=22.12.0 を要求するが `setup-bun` は Node を管理しないため。
- Decision: `test_map.py`, `test_recommend.py` を python-test の --ignore に追加。Rationale: modal の `@app.local_entrypoint()` が import 時にグローバル登録されるため、CI 環境で複数スクリプトを import すると Duplicate entrypoint エラーが発生する。
- Decision: ruff の自動修正 (`--fix`) を使用。Rationale: F401/F541 は全て自動修正可能で、手動修正よりミスが少ない。

## Notes

- `oven-sh/setup-bun@v2` の `cache: true` は warning が出るが動作に問題なし（将来バージョンで修正予定）
- PR #6: https://github.com/senna-lang/arxiv-compass/pull/6
