from __future__ import annotations

import argparse
import time
import requests
import osmnx as ox

from poi_db import replace_pois, count_pois

OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

QUERIES = {
    "street_lamp": """
      node["highway"="street_lamp"]({s},{w},{n},{e});
      node["man_made"="street_lamp"]({s},{w},{n},{e});
      node["amenity"="street_lamp"]({s},{w},{n},{e});
    """,
    "convenience": """
      node["shop"="convenience"]({s},{w},{n},{e});
      way["shop"="convenience"]({s},{w},{n},{e});
    """,
    "police": """
      node["amenity"="police"]({s},{w},{n},{e});
      way["amenity"="police"]({s},{w},{n},{e});
      node["police"]({s},{w},{n},{e});
      way["police"]({s},{w},{n},{e});
    """,
}


def get_bbox(place: str):
    gdf = ox.geocode_to_gdf(place)
    west, south, east, north = gdf.total_bounds
    return south, west, north, east


def fetch(query: str):
    last = None
    for url in OVERPASS_URLS:
        try:
            r = requests.post(
                url,
                data=f"[out:json][timeout:180];({query});out center;",
                timeout=210,
            )
            r.raise_for_status()
            return r.json().get("elements", [])
        except Exception as e:
            last = e
            time.sleep(2)
    raise RuntimeError(f"Overpass取得失敗: {last}")


def normalize(elements):
    out = []
    for el in elements:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is not None and lon is not None:
            out.append((float(lat), float(lon), el.get("tags", {})))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--place", default="さいたま市, 埼玉, Japan")
    args = parser.parse_args()

    bbox = get_bbox(args.place)
    s, w, n, e = bbox
    print(f"対象範囲: south={s}, west={w}, north={n}, east={e}")

    for poi_type, template in QUERIES.items():
        print(f"\n{poi_type} をOverpassから取得中...")
        rows = normalize(fetch(template.format(s=s, w=w, n=n, e=e)))
        count = replace_pois(poi_type, rows)
        print(f"{count}件を data/osm_poi.db に保存しました。")

    print("\n保存結果:", count_pois())


if __name__ == "__main__":
    main()
