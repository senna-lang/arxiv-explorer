## Key Specification

`[date].astro` を2カラムレイアウトに変更し、SerendipitySection を組み込む。

## What Was Done

- `SerendipitySection` をインポート
- `body` の max-width を 800px → 1200px に変更
- `.papers-section { max-width: 800px; margin: 0 auto; }` を追加し、論文カードを10件ずつラップ
- `RecommendSection` と `SerendipitySection` を `.bottom-columns` グリッドに並列配置
- レスポンシブ: 768px以下で1カラムにフォールバック

## How It Was Done

papers.slice(0, 10) / papers.slice(10) で分割。11件未満の場合は後半セクションをスキップ。

## Gotchas & Lessons Learned

`.papers-section` の max-width は `body` のそれとは独立して設定する必要がある。

## Reusable Patterns

`.bottom-columns` グリッドパターンは他のページにも転用可能。
