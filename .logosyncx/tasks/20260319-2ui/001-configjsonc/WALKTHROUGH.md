## Key Specification

`config.jsonc` の `recommendation` セクションにセレンディピティ用パラメータを追加する。

## What Was Done

`recommendation` セクションの `min_match_score` 直後に4項目を追加:
- `serendipity_clusters: 3`
- `serendipity_top_n: 10`
- `serendipity_min_match_score: 0.45`
- `serendipity_max_match_score: 0.65`

## How It Was Done

既存の JSONC 構文に合わせてコメント付きで追記。

## Gotchas & Lessons Learned

特になし。

## Reusable Patterns

特になし。
