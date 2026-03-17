---
id: t-6d78cb
date: 2026-03-17T22:17:23.672078+09:00
title: GitHub Actions workflow 3本作成（daily/weekly/monthly）
seq: 7
status: done
priority: high
plan: 20260315-
depends_on:
    - 4
    - 5
    - 6
tags: []
assignee: ""
completed_at: 2026-03-17T23:07:32.404343+09:00
---

## What

GitHub Actions の workflow ファイル 3本（daily.yml / weekly.yml / monthly.yml）を作成する。各 workflow は Modal でバッチを実行し、生成 JSON を git commit して CF Pages にデプロイする。

## Why

スケジュール実行の起点。ローカルマシン依存をなくし arXiv新聞を完全自律運用にする。

## Scope

- `.github/workflows/daily.yml`（新規）
- `.github/workflows/weekly.yml`（新規）
- `.github/workflows/monthly.yml`（新規）

## Acceptance Criteria

- [ ] daily.yml: 月〜金 09:00 JST に自動実行、`workflow_dispatch` で手動実行可
- [ ] weekly.yml: 月曜 09:30 JST に自動実行
- [ ] monthly.yml: 毎月1日 10:00 JST に自動実行
- [ ] 各 workflow で `modal run` → `npm run build` → `wrangler pages deploy` → `git push` が通る

## Checklist

- [ ] `.github/workflows/` ディレクトリ作成
- [ ] daily.yml 作成（cron: `0 0 * * 1-5`）
- [ ] weekly.yml 作成（cron: `30 0 * * 1`）
- [ ] monthly.yml 作成（cron: `0 1 1 * *`）
- [ ] 必要シークレットを GitHub リポジトリに登録: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`
- [ ] `workflow_dispatch` で daily.yml を手動実行して疎通確認

## Notes

各 workflow の共通ステップ:
1. `pip install modal`
2. `modal token set --token-id $MODAL_TOKEN_ID --token-secret $MODAL_TOKEN_SECRET`
3. `modal run scripts/xxx.py`
4. `npm ci && npm run build`
5. `npx wrangler pages deploy dist/ --project-name arxiv-newspaper`
6. `git config user.email "..." && git add data/ && git commit -m "chore: daily batch YYYYMMDD" && git push`

シークレット一覧:
| シークレット | 用途 |
|---|---|
| `MODAL_TOKEN_ID` | modal CLI 認証 |
| `MODAL_TOKEN_SECRET` | modal CLI 認証 |
| `CLOUDFLARE_API_TOKEN` | wrangler deploy |
| `CLOUDFLARE_ACCOUNT_ID` | wrangler deploy |
