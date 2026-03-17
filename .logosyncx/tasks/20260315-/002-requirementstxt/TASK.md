---
id: t-824011
date: 2026-03-17T22:17:08.374751+09:00
title: requirements.txt 作成
seq: 2
status: done
priority: high
plan: 20260315-
tags: []
assignee: ""
completed_at: 2026-03-17T23:00:43.582847+09:00
---

## What

GitHub Actions および Modal 環境で Python バッチを実行するための `requirements.txt` を作成する。現状 requirements.txt が存在しないため CI での pip install ができない。

## Why

GitHub Actions workflow の `pip install -r requirements.txt` と Modal image の `pip_install()` の両方で参照するために必要。

## Scope

- `requirements.txt`（新規作成）

OUT of scope: pyproject.toml / poetry への移行

## Acceptance Criteria

- [ ] `requirements.txt` が存在する
- [ ] `modal` パッケージが含まれている
- [ ] `pip install -r requirements.txt` がエラーなく通る

## Checklist

- [ ] 既存スクリプトの import を全確認して依存を列挙
- [ ] `requirements.txt` 作成
- [ ] ローカルで `pip install -r requirements.txt` を確認

## Notes

必要パッケージ（暫定）:
- arxiv
- numpy
- sentence-transformers
- torch（CPU版で可、Modal 側は CUDA 版を image で別途指定）
- bertopic
- datamapplot
- umap-learn
- hdbscan
- modal
