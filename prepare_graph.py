from __future__ import annotations

import argparse
from pathlib import Path
import osmnx as ox

GRAPH_DIR = Path("data/graphs")
GRAPH_DIR.mkdir(parents=True, exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", default="さいたま市, 埼玉, Japan")
    parser.add_argument("--network-type", default="walk")
    args = parser.parse_args()

    # Windows/OSMnxで安全に扱えるファイル名
    safe = "".join(c if c.isalnum() else "_" for c in args.place).strip("_")
    path = GRAPH_DIR / f"{safe}_{args.network_type}.graphml"

    if path.exists():
        print(f"既に存在します: {path}")
        return

    print(f"道路ネットワークを事前取得中: {args.place}")
    G = ox.graph_from_place(args.place, network_type=args.network_type)
    ox.save_graphml(G, path)
    print(f"保存しました: {path}")


if __name__ == "__main__":
    main()
