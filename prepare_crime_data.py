from __future__ import annotations

import glob
import argparse
from pathlib import Path
import pandas as pd
import osmnx as ox
import time


def geocode(query: str):
    return ox.geocode(query)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/")
    parser.add_argument("--output", default="data/crime_geocoded.csv")
    args = parser.parse_args()

    files = glob.glob(str(Path(args.input) / "*.csv"))
    rows = []

    for path in files:
        # 既に出力したファイルは除外
        if Path(path).name == Path(args.output).name:
            continue

        df = None
        for enc in ("utf-8-sig", "utf-8", "cp932", "shift_jis"):
            try:
                df = pd.read_csv(path, encoding=enc)
                break
            except Exception:
                pass

        if df is None:
            print(f"読み込み失敗: {path}")
            continue

        required = {"市区町村（発生地）", "町丁目（発生地）"}
        if not required.issubset(df.columns):
            continue

        addresses = (
            df["市区町村（発生地）"].astype(str)
            + df["町丁目（発生地）"].astype(str)
        ).dropna().unique()

        for address in addresses:
            try:
                lat, lon = geocode(address)
                rows.append({"address": address, "lat": lat, "lon": lon})
                print(f"OK: {address}")
            except Exception as e:
                print(f"NG: {address} -> {e}")
            time.sleep(1)

    out = pd.DataFrame(rows).drop_duplicates("address")
    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"\n{len(out)}件を {args.output} に保存しました。")


if __name__ == "__main__":
    main()
