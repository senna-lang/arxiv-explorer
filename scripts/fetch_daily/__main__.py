"""python -m scripts.fetch_daily のエントリポイント"""
from .cli import main
from datetime import datetime
from core.config import JST
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--date", default=datetime.now(JST).strftime("%Y%m%d"))
parser.add_argument("--log", action="store_true")
args = parser.parse_args()
main(args.date, log=args.log)
