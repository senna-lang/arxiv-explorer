# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# フロントエンド
npm run dev          # 開発サーバー起動
npm run build        # 本番ビルド
npm run preview      # ビルド結果をプレビュー

# Pythonパイプライン
npm run parse        # 今日の trend.md をパースして YYYYMMDD.json を生成
npm run parse:all    # data/ にない日付の trend.md を一括処理
npm run map          # 論文地図を生成（max 1000件）
npm run map:full     # 論文地図を生成（max 10000件）
npm run recommend    # おすすめ論文を生成

# KVへのデータ移行
npx wrangler kv key put "ratings" --namespace-id=797a1d2d28ef40cd86bb25c2bce60fe9 --path=data/ratings.json --remote

# 型チェック
npx tsc --noEmit
```

## アーキテクチャ

### データフロー

```
daily-news skill → YYYYMMDD-trend.md（config.trend_dir に保存）
    ↓
parse.py → data/YYYYMMDD.json（arXiv論文 + スコア）
    ↓
Astro static build → Cloudflare Pages にデプロイ

ユーザーが星をつける
    ↓
POST /api/rate → Cloudflare KV（RATINGS_KV）
GET /api/ratings → recommend.py が ratings_url 経由で取得
    ↓
recommend.py → data/recommendations.json
```

### フロントエンド（Astro + Cloudflare）

- `output: 'static'` で静的ビルド。`/api/*` エンドポイントだけ `prerender = false` でWorkerとして動作
- ページは `import.meta.glob("/data/????????.json", { eager: true })` でビルド時にJSONを読み込む（`node:fs` は使わない）
- KVバインディングは `import { env } from "cloudflare:workers"` でアクセス。型は `src/env.d.ts` の `Cloudflare.Env` で定義
- 共通レイアウトは `src/layouts/MainLayout.astro`。ページ固有のスタイルは `<style slot="head">` で注入

### Pythonパイプライン

- `config.json` が全スクリプトの設定起点（`embedding_model`, `trend_dir`, `output_dir`, `ratings_url` など）
- 全スクリプトが同じモデル `allenai/specter2_base` を使用
- `recommend.py` は `config.ratings_url`（本番: `GET /api/ratings`）から評価データを取得。未設定時は `data/ratings.json` にフォールバック

### スコアリングロジック

- 日次: `abstract` vs `interest_profile`（7項目）の cosine similarity 平均 = score
- 週次レコメンド: `α = min(1.0, ratings件数/50)` で profile ベースから実績ベースへ段階的移行

## 重要な制約

- `import.meta.glob()` は Vite の制約でユーティリティ関数内に書けない。各ページファイルで直接呼ぶ必要がある。日付リストへの変換は `extractDates()` (`src/lib/data.ts`) で共通化
- `data/ratings.json` はKV移行済みのため、ランタイムでは使用されない。バッチスクリプト実行時は `ratings_url` 経由でKVから取得する

# Agent Instructions

This project uses **logos** for plan and task tracking, stored in `.logosyncx/`.

## Task Tracking

```bash
logos task ls --status open --json                        # Find available work
logos task refer --name <name>                            # View task details
logos task update --name <name> --status in_progress      # Claim a task
logos task update --name <name> --status done             # Complete a task
logos sync                                                # Rebuild plan and task indexes
```

**Session completion is mandatory** — see the workflow below.

## MANDATORY: logos Command Triggers

The following triggers are **not optional**. When any of these conditions occur, you MUST run the corresponding command immediately.

### Starting any work session

**ALWAYS run this first, before doing anything else:**

```bash
logos ls --json
```

Scan the `topic`, `tags`, and `excerpt` fields to find relevant past plans.
If anything looks relevant, run:

```bash
logos refer --name <filename> --summary
```

### Mid-session triggers

| If the user says (any variation) | You MUST run |
|---|---|
| "save this plan", "log this", "記録して" | `logos save --topic "..."` then write body with Write tool |
| "make that a task", "タスクにして" | `logos task create --plan <name> --title "..."` |
| "what did we do last time", "前回の続き" | `logos ls --json` then `logos refer --name <name>` |
| "continue from last session", "前回の続きから" | `logos ls --json` -> find latest relevant -> `logos refer --name <name>` |

### When saving a plan

```bash
logos save --topic "short description" --tag <tag> --agent <agent-name>
```

Then immediately write the body — **a plan without a body is broken**:

```bash
# 1. Read the plan template
cat .logosyncx/templates/plan.md

# 2. Write the body directly into the plan file using the Write tool
#    (append after the closing --- of the frontmatter)
```

Do NOT use `--section` flags — they do not exist in v2.

### When creating a task

**CRITICAL: Create tasks ONE AT A TIME. A task without a body is broken.**

For each task, follow this exact sequence before creating the next:

```bash
# 1. Create the task
logos task create --plan <plan-slug> --title "Implement the thing" --priority high

# 2. Read the template
cat .logosyncx/templates/task.md

# 3. Write the body into the created TASK.md using the Write tool
#    (path printed by logos task create)
```

Do NOT batch-create multiple tasks without filling the body for each one first.

---

## Landing the Plane (Session Completion)

**When ending a work session**, complete ALL steps below. Work is NOT complete until `git push` succeeds.

1. **File tasks for remaining work:**
   ```bash
   logos task create --plan <plan-slug> --title "..."
   ```
2. **Run quality gates** (if code changed): `go test ./...`
3. **Write WALKTHROUGH.md, then mark done** — this order is enforced by the CLI:
   ```bash
   # a. Read the template
   cat .logosyncx/templates/walkthrough.md
   # b. Write content into the task's WALKTHROUGH.md using the Write tool
   #    (path: .logosyncx/tasks/<plan-slug>/<NNN-task-name>/WALKTHROUGH.md)
   # c. Only after writing — mark done
   logos task update --name <name> --status done
   ```
4. **Save this plan:**
   ```bash
   logos save --topic "..."
   # Write the body into the plan file
   ```
5. **PUSH TO REMOTE** — MANDATORY:
   ```bash
   git pull --rebase
   logos sync
   git add .logosyncx/
   git commit -m "logos: save plan \"<topic>\""
   git push
   ```
6. **Verify** — `git status` MUST show "up to date with origin"

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing
- Always read the template before writing any document body

---

## Full Command Reference

See `.logosyncx/USAGE.md` for the complete command reference.


## Code Intelligence

Prefer LSP over Grep/Read for code navigation — it's faster, precise, and avoids reading entire files:
- `workspaceSymbol` to find where something is defined
- `findReferences` to see all usages across the codebase
- `goToDefinition` / `goToImplementation` to jump to source
- `hover` for type info without reading the file

Use Grep only when LSP isn't available or for text/pattern searches (comments, strings, config).

After writing or editing code, check LSP diagnostics and fix errors before proceeding.
