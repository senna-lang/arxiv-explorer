## Key Specification

map.astroでUMAP 2D座標をCanvasに散布図描画。近傍クラスタをオレンジでハイライト。

## What Was Done

- `src/pages/map.astro`: Canvas描画 + ツールチップ + 近傍ハイライト
- `[date].astro`に地図へのリンクを追加

## How It Was Done

`define:vars`でAstroのサーバーサイドデータをクライアントJSに渡す。
UMAP座標をCanvas座標にスケーリングして描画。円サイズはsqrt(size/maxSize)*22。

## Gotchas & Lessons Learned

- `define:vars={{ clustersJson, nearLabelsJson }}`でJSON文字列をクライアントに渡す

## Reusable Patterns

```astro
<script define:vars={{ dataJson }}>
  const data = JSON.parse(dataJson);
  // クライアントサイドで使用
</script>
```
