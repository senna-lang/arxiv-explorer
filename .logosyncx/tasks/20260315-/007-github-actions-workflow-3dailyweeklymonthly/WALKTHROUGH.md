## Key Specification

GitHub Actions で日次・週次・月次バッチを自動実行。各 workflow は Modal でバッチを動かし、生成 JSON を git commit → CF Pages デプロイする。

## What Was Done

`.github/workflows/` に 3 本の workflow を作成:
- `daily.yml`: 月〜金 09:00 JST、fetch_daily.py
- `weekly.yml`: 月曜 09:30 JST、recommend.py
- `monthly.yml`: 毎月1日 10:00 JST、map.py → recommend.py

## How It Was Done

共通構造:
1. Python 3.11 + `pip install -r requirements.txt`
2. `modal token set` でシークレットから認証
3. Node 20 + `npm ci`
4. `USE_MODAL=1 modal run scripts/xxx.py --log`
5. `npm run build` → `wrangler pages deploy`
6. `git add data/ && git commit && git push`

`git diff --cached --quiet || git commit` で差分がない場合はコミットをスキップする。

## Gotchas & Lessons Learned

- `actions/checkout` の `token: ${{ secrets.GITHUB_TOKEN }}` が必要（デフォルトトークンでは push できない）
- `git diff --cached --quiet || git commit` で「変更なしのとき失敗しない」ようにする
- monthly.yml は map.py の後に recommend.py も実行（map.json が変わるため）

## Reusable Patterns

```yaml
- name: Commit generated JSON
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/
    git diff --cached --quiet || git commit -m "chore: daily batch $(date +%Y%m%d)"
    git push
```
