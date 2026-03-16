"""
ベンチマーク専用スクリプト。各パイプラインを --log 付きで実行し、結果をサマリー表示する。

実行:
    python scripts/benchmark.py                  # recommend + fetch_daily
    python scripts/benchmark.py --map            # map も含む（重い: ~500秒）
    python scripts/benchmark.py --only recommend # recommend のみ

ログは各スクリプトと共通の JSONL ファイルに追記される:
    data/recommend_runs.jsonl
    data/fetch_daily_runs.jsonl
    data/map_runs.jsonl
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
JST = ZoneInfo("Asia/Tokyo")

# 同ディレクトリの各スクリプトを import できるようにする
sys.path.insert(0, str(Path(__file__).parent))

# ── ANSI カラー ──────────────────────────────────────────────────────────────
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _header(title: str) -> None:
    width = 60
    print(f"\n{BOLD}{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * width}{RESET}")


def _last_entry(jsonl_path: Path) -> dict | None:
    """JSONL ファイルの最終行を返す。"""
    if not jsonl_path.exists():
        return None
    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    return json.loads(lines[-1]) if lines else None


def _print_recommend_summary(entry: dict) -> None:
    print(
        f"  {BOLD}alpha{RESET}            : {entry['alpha']:.2f}  "
        f"(ratings={entry['n_ratings']})"
    )
    print(f"  {BOLD}n_recommendations{RESET}: {entry['n_recommendations']}")
    ms = entry.get("match_score", {})
    print(
        f"  {BOLD}match_score{RESET}      : "
        f"min={ms.get('min')}  mean={ms.get('mean')}  max={ms.get('max')}"
    )
    print(f"  {BOLD}top clusters{RESET}     :")
    for c in entry.get("top_clusters", []):
        print(f"      {c['score']:.4f}  {c['label']}")
    print(f"  {BOLD}elapsed{RESET}          : {entry['elapsed_sec']}s")


def _print_fetch_daily_summary(entry: dict) -> None:
    print(f"  {BOLD}date{RESET}         : {entry['date']}")
    print(
        f"  {BOLD}alpha{RESET}        : {entry['alpha']:.2f}  "
        f"(ratings={entry['n_ratings']})"
    )
    print(
        f"  {BOLD}n_candidates{RESET} : {entry['n_candidates']}  "
        f"→ n_papers={entry['n_papers']}"
    )
    sc = entry.get("score", {})
    print(
        f"  {BOLD}score{RESET}        : "
        f"min={sc.get('min')}  mean={sc.get('mean')}  max={sc.get('max')}"
    )
    if entry.get("top_paper"):
        print(f"  {BOLD}top paper{RESET}    : {entry['top_paper'][:60]}")
    print(f"  {BOLD}elapsed{RESET}      : {entry['elapsed_sec']}s")


def _print_map_summary(entry: dict) -> None:
    print(f"  {BOLD}fetched{RESET}          : {entry['fetched']}")
    print(f"  {BOLD}n_clusters{RESET}       : {entry['n_clusters']}")
    print(
        f"  {BOLD}noise_pct{RESET}        : {entry['noise_pct']}%  "
        f"({entry['noise']} papers)"
    )
    cs = entry.get("cluster_size", {})
    print(
        f"  {BOLD}cluster_size{RESET}     : "
        f"min={cs.get('min')}  mean={cs.get('mean')}  max={cs.get('max')}"
    )
    print(f"  {BOLD}min_cluster_size{RESET} : {entry['min_cluster_size']}")
    print(f"  {BOLD}elapsed{RESET}          : {entry['elapsed_sec']}s")
    if entry.get("cluster_labels"):
        print(f"  {BOLD}cluster_labels{RESET}   :")
        for label in entry["cluster_labels"]:
            print(f"      {label}")


# ── ベンチマーク実行 ─────────────────────────────────────────────────────────


def run_recommend() -> dict | None:
    _header("recommend.py")
    from recommend import main as recommend_main

    config_path = ROOT / "config.jsonc"
    import re

    text = config_path.read_text(encoding="utf-8")
    text = re.sub(
        r'"[^"\\]*(?:\\.[^"\\]*)*"|//[^\n]*',
        lambda m: m.group(0) if m.group(0).startswith('"') else "",
        text,
    )
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    config = json.loads(text)
    rec_cfg = config.get("recommendation", {})

    recommend_main(
        top_clusters=rec_cfg.get("top_clusters", 3),
        top_n=rec_cfg.get("top_n", 20),
        log=True,
    )
    return _last_entry(DATA_DIR / "recommend_runs.jsonl")


def run_fetch_daily() -> dict | None:
    _header("fetch_daily.py")
    from fetch_daily import main as fetch_main

    date_str = datetime.now(JST).strftime("%Y%m%d")
    fetch_main(date_str, log=True)
    return _last_entry(DATA_DIR / "fetch_daily_runs.jsonl")


def run_map(max_papers: int) -> dict | None:
    _header(f"map.py (max_papers={max_papers})")
    from map import main as map_main

    map_main(max_papers, log=True)
    return _last_entry(DATA_DIR / "map_runs.jsonl")


# ── メイン ───────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run pipeline benchmarks and print a summary"
    )
    parser.add_argument(
        "--only",
        choices=["recommend", "daily", "map"],
        help="Run only one script (default: recommend + daily)",
    )
    parser.add_argument(
        "--map",
        action="store_true",
        help="Also run map.py (slow: ~500s for 10,000 papers)",
    )
    parser.add_argument(
        "--map-papers",
        type=int,
        default=1000,
        help="max_papers for map.py when --map is set (default: 1000)",
    )
    args = parser.parse_args()

    started = time.time()
    results: dict[str, dict | None] = {}

    if args.only == "recommend":
        results["recommend"] = run_recommend()
    elif args.only == "daily":
        results["daily"] = run_fetch_daily()
    elif args.only == "map":
        results["map"] = run_map(args.map_papers)
    else:
        results["recommend"] = run_recommend()
        results["daily"] = run_fetch_daily()
        if args.map:
            results["map"] = run_map(args.map_papers)

    # ── サマリー表示 ─────────────────────────────────────────────────────────
    width = 60
    print(f"\n{BOLD}{GREEN}{'═' * width}{RESET}")
    print(
        f"{BOLD}{GREEN}  BENCHMARK SUMMARY  "
        f"(total {round(time.time() - started, 1)}s){RESET}"
    )
    print(f"{BOLD}{GREEN}{'═' * width}{RESET}")

    if "recommend" in results:
        print(f"\n{YELLOW}[recommend]{RESET}")
        entry = results["recommend"]
        if entry:
            _print_recommend_summary(entry)
        else:
            print("  (no log entry found)")

    if "daily" in results:
        print(f"\n{YELLOW}[fetch_daily]{RESET}")
        entry = results["daily"]
        if entry:
            _print_fetch_daily_summary(entry)
        else:
            print("  (no log entry found)")

    if "map" in results:
        print(f"\n{YELLOW}[map]{RESET}")
        entry = results["map"]
        if entry:
            _print_map_summary(entry)
        else:
            print("  (no log entry found)")

    print()


if __name__ == "__main__":
    main()
