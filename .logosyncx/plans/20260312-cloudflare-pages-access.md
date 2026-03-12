---
id: 707a8a
topic: Cloudflare Pages デプロイ + Access 認証
tags:
    - cloudflare
    - deploy
agent: claude-code
related: []
tasks_dir: .logosyncx/tasks/20260312-cloudflare-pages-access
distilled: false
---

## Context

現在のアプリはローカル専用（@astrojs/node）で、rate.tsがexecSyncでgit pushしている。
Cloudflare Pagesにデプロイして自分だけがアクセスできるようにする。

核心的な変更:
- ページを静的プリレンダリングに切り替え → CF Pagesで高速配信
- rate.tsのgit pushをGitHub REST APIに置き換え → サーバーレス環境対応
- Cloudflare Accessで自分のメールだけアクセス許可

## Architecture

```
ビルド時（Node.js）
  data/*.json → readFileSync で読み込み → 全ページをHTML生成（静的）

デプロイ後（Cloudflare Pages）
  CF Access → メール認証 → 静的HTMLを配信
  星クリック → POST /api/rate（CF Worker）
            → GitHub REST API で ratings.json を更新
            → CF Pages が自動リビルド（数分後）
            → 画面はrate.jsで楽観的UI更新（即時）
```

## Changes

| ファイル | 変更内容 |
|---------|---------|
| `astro.config.mjs` | @astrojs/cloudflare に切り替え |
| `package.json` | @astrojs/cloudflare 追加、@astrojs/node 削除 |
| `wrangler.toml` | 新規作成（nodejs_compat フラグ） |
| `src/pages/[date].astro` | prerender=false → getStaticPaths() に変更 |
| `src/pages/map.astro` | prerender=false を削除（静的化） |
| `src/pages/api/rate.ts` | execSync(git push) → GitHub REST API |

## rate.ts GitHub API Flow

環境変数: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO

1. GET /repos/{owner}/{repo}/contents/data/ratings.json → base64デコード + SHA取得
2. ratings配列を更新（既存は上書き、新規は追加）
3. PUT /repos/{owner}/{repo}/contents/data/ratings.json → base64エンコードして上書きコミット
4. 200 OK を返す

## Deploy Flow

1. bun add @astrojs/cloudflare
2. bun remove @astrojs/node
3. コード変更（上記）
4. git push → CF Pagesがビルド＆デプロイ
5. CF Pages Settings > Environment variables に GITHUB_TOKEN 等を設定
6. CF Access で URL 保護設定（Zero Trust → Access → Applications）

## CF Access 設定（ダッシュボード）

Zero Trust → Access → Applications → Add application
  → Self-hosted
  → Application domain: <app>.pages.dev
  → Policy: Include > Emails > [自分のメールアドレス]

## Verification

1. bun run build でエラーなし確認
2. CF Pagesのプレビューで全ページ表示確認
3. 星クリック → ratings.jsonにコミットが来ることをGitHub上で確認
4. CF Accessで未認証アクセスが弾かれることを確認
