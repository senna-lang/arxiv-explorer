---
id: t-240fea
date: 2026-03-12T10:31:00.609527+09:00
title: embedding_modelをspecter2に移行
seq: 1
status: done
priority: medium
plan: 20260312-arxiv-phase-2
tags: []
assignee: ""
completed_at: 2026-03-12T10:34:53.000018+09:00
---

## What

`config.json`の`embedding_model`を`all-MiniLM-L6-v2`から`allenai/specter2`に変更する。
map.py・recommend.pyと同一ベクトル空間を使うために必要。parse.py本体は変更不要。

## Why

map.pyとrecommend.pyはspecter2を使う。parse.pyが異なるモデルだとベクトル空間がズレ、
recommend.pyのスコアリングが無意味になる。

## Scope

- `config.json`（embedding_modelフィールドのみ）

OUT: parse.py本体（モデル名はconfig.jsonから読み込むため変更不要）

## Acceptance Criteria

- [ ] `config.json`の`embedding_model`が`"allenai/specter2"`
- [ ] 既存テスト13件がPASS

## Checklist

- [ ] `config.json`の`embedding_model`を`"allenai/specter2"`に変更
- [ ] `python -m pytest scripts/tests/ -v`でPASS確認

## Notes

- specter2はsentence-transformersから直接ロード可能
- 初回ダウンロード約500MB
- 既存のdata/YYYYMMDD.jsonはall-MiniLM-L6-v2製のためPhase 2移行後は再生成が必要
