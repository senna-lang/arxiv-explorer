---
id: t-00dd56
date: 2026-03-19T22:44:17.735541+09:00
title: '[date].astro を2カラムレイアウトに変更'
seq: 5
status: done
priority: high
plan: 20260319-2ui
tags: []
assignee: ""
completed_at: 2026-03-20T00:03:48.606551+09:00
---

## What

`src/pages/[date].astro` を2カラムレイアウトに変更する。daily論文は `papers-section` でラップして max-width: 800px を維持しつつ、下部に CSS Grid 2カラムで「おすすめ」と「こんなのもどう？」を左右に並べる。モバイルでは1カラムにフォールバック。

## Why

UIの情報密度を上げ、おすすめとセレンディピティを並列で閲覧しやすくする。

## Scope

- `src/pages/[date].astro`

## Acceptance Criteria

- [ ] daily論文が `papers-section` にラップされ max-width: 800px が維持される
- [ ] 下部に `.bottom-columns` グリッドが存在し、左=RecommendSection、右=SerendipitySection
- [ ] `body` の max-width が 1200px に変更されている
- [ ] 768px以下で1カラムに切り替わる
- [ ] `npm run build` が成功する

## Checklist

- [ ] `SerendipitySection` をインポート
- [ ] `body { max-width: 800px }` → `body { max-width: 1200px }`
- [ ] `.papers-section { max-width: 800px; margin: 0 auto; }` を追加
- [ ] PaperCard を `.papers-section` でラップ
- [ ] `<RecommendSection />` を `.bottom-columns` グリッドに移動
- [ ] `<SerendipitySection />` を右カラムに追加
- [ ] レスポンシブメディアクエリ追加
- [ ] `npx tsc --noEmit` → `npm run build` で確認

## Notes

papers.slice(0, 10) と papers.slice(10) で10件ずつに分割してセクションを区切る。
