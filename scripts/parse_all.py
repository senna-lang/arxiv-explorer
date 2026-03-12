"""
trend_dir 内の全 YYYYMMDD-trend.md を対象に parse.py を実行する。

既に data/YYYYMMDD.json が存在する日付はスキップする（--force で強制上書き）。

実行:
    python scripts/parse_all.py
    python scripts/parse_all.py --force
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config.json"


def main(force: bool) -> None:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = json.load(f)

    trend_dir = Path(config["trend_dir"])
    output_dir = ROOT / config["output_dir"]

    if not trend_dir.exists():
        print(f"[ERROR] trend_dir not found: {trend_dir}")
        sys.exit(1)

    trend_files = sorted(trend_dir.glob("*-trend.md"))
    if not trend_files:
        print(f"[WARN] No trend.md files found in {trend_dir}")
        return

    print(f"[INFO] Found {len(trend_files)} trend files")

    ok = skipped = failed = 0
    for path in trend_files:
        m = re.match(r"(\d{8})-trend\.md$", path.name)
        if not m:
            continue
        date = m.group(1)

        out = output_dir / f"{date}.json"
        if out.exists() and not force:
            print(f"[SKIP] {date} (already exists)")
            skipped += 1
            continue

        print(f"[RUN]  {date} ...")
        result = subprocess.run(
            [sys.executable, "scripts/parse.py", "--date", date],
            cwd=ROOT,
        )
        if result.returncode == 0:
            ok += 1
        else:
            print(f"[FAIL] {date}")
            failed += 1

    print(f"\n[DONE] ok={ok}  skipped={skipped}  failed={failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run parse.py for all trend.md files")
    parser.add_argument("--force", action="store_true", help="Re-parse even if JSON already exists")
    args = parser.parse_args()
    main(args.force)
