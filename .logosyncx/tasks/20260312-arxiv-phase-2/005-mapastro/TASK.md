---
id: t-d105bc
date: 2026-03-12T10:31:00.634881+09:00
title: map.astro 地図可視化
seq: 5
status: done
priority: medium
plan: 20260312-arxiv-phase-2
tags: []
assignee: ""
completed_at: 2026-03-12T10:46:47.51981+09:00
---

## What

`src/pages/map.astro`を実装する。map.jsonのUMAP 2D座標を使い、
arXivの論文クラスタをインタラクティブな散布図で可視化する。

## Why

「地図上の自分の位置」を視覚的に確認することでPhase 2の発見体験が完成する。

## Scope

- `src/pages/map.astro`
- `src/lib/data.ts`（getMap()を追加）
- `src/lib/types.ts`（Cluster/MapData型を追加）

## Acceptance Criteria

- [ ] 各クラスタが2D散布図上の円で表示される（sizeに比例した大きさ）
- [ ] 近傍クラスタ（recommendations.jsonのtop_clusters）がハイライト表示される
- [ ] ホバーでクラスタラベルと論文数がツールチップ表示される
- [ ] map.jsonがなければ「地図未生成」メッセージを表示
- [ ] `bun run build`でエラーなし

## Checklist

- [ ] `src/lib/types.ts`にCluster/MapData型を追加
- [ ] `src/lib/data.ts`に`getMap()`を追加
- [ ] `src/pages/map.astro`を実装
  - [ ] `export const prerender = false`
  - [ ] map.json + recommendations.jsonを読み込み
  - [ ] Canvas要素にクラスタを描画（vanilla JS）
  - [ ] UMAP座標をCanvas座標に変換（スケーリング）
  - [ ] 近傍クラスタを別色でハイライト
  - [ ] mousemoveでツールチップ表示
- [ ] `[date].astro`のヘッダーに地図ページへのリンクを追加

## Notes

- Canvas描画はAstroの`<script>`タグ内に記述
- UMAP座標の範囲は動的に計算してフィットさせる
- 円サイズ: `r = sqrt(cluster.size) * 定数` でsizeに比例
