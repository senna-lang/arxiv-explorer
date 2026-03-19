---
id: t-41f2e5
date: 2026-03-19T22:43:56.530671+09:00
title: SerendipitySection.astro コンポーネントを作成
seq: 4
status: open
priority: high
plan: 20260319-2ui
tags: []
assignee: ""
---

## What

`src/components/SerendipitySection.astro` を新規作成する。`RecommendSection.astro` をベースに、タイトル・ラベル・カラースキーム（緑系）を変更し、`data.serendipity` / `data.serendipity_clusters` を表示する。

## Why

「こんなのもどう？」セクションのUIコンポーネント。おすすめセクションと視覚的に区別しつつ同じインタラクション（星評価、abstractトグル）を提供する。

## Scope

- `src/components/SerendipitySection.astro` (新規)
- `src/components/RecommendSection.astro` (border-top / margin-top を削除 — 親で制御)

OUT: ページへの組み込み（タスク5で行う）

## Acceptance Criteria

- [ ] `data.serendipity` が空/未定義の場合は何も表示しない
- [ ] 緑系カラースキーム（`#059669` / `#d1fae5`）が適用されている
- [ ] タイトルが「🌱 こんなのもどう？」
- [ ] クラスタラベルが「探索クラスタ:」
- [ ] 星評価と abstract トグルが動作する

## Checklist

- [ ] `RecommendSection.astro` を参考に構造をコピー
- [ ] タイトル・ラベル・色を変更
- [ ] データソースを `data.serendipity` / `data.serendipity_clusters` に変更
- [ ] `RecommendSection.astro` から `border-top` / `margin-top` を `.recommend-section` から削除

## Notes

- 星評価のJSは `RecommendSection.astro` と同じスクリプトパターンを使用
- カラースキーム: cluster-tag に `background: #d1fae5; color: #059669; border-color: #a7f3d0`
