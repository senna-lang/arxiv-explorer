---
id: t-f82bd7
date: 2026-03-20T12:50:07.197176+09:00
title: 'CI 検証: feature ブランチで PR 作成・動作確認'
seq: 4
status: done
priority: high
plan: 20260320-ci
tags: []
assignee: ""
completed_at: 2026-03-20T13:10:56.045939+09:00
---

## What

feature ブランチを作成して ci.yml を push し、PR を作成して 4 ジョブが並列で走ることを確認する。失敗があれば修正する。

## Why

CI ワークフローが意図通りに動作することを実環境で検証するため。

## Scope

- PR 作成・動作確認
- 失敗ジョブの修正

## Acceptance Criteria

- [ ] PR で 4 ジョブ（typecheck, astro-build, python-test, python-lint）が並列実行される
- [ ] typecheck: 型エラーなしで pass
- [ ] astro-build: dist/ が生成されて pass
- [ ] python-test: テスト全件 pass
- [ ] python-lint: ruff エラーがあれば修正して pass

## Checklist

- [ ] feature ブランチ作成・push
- [ ] PR 作成
- [ ] 4 ジョブの結果確認
- [ ] 失敗があれば修正・再 push

## Notes

- ruff の既定ルールで lint エラーが出る可能性あり。初回は修正対応する
