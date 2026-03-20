"""python -m scripts.recommend のエントリポイント"""
from .cli import main
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--top-clusters", type=int, default=3)
parser.add_argument("--top-n", type=int, default=20)
parser.add_argument("--log", action="store_true")
args = parser.parse_args()
main(args.top_clusters, args.top_n, log=args.log)
