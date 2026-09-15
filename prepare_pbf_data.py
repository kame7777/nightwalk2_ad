from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import requests
import osmium

PBF_URL = "https://download.geofabrik.de/asia/japan/kanto-latest.osm.pbf"
DEFAULT_PBF = Path("data/kanto-latest.osm.pbf")
DEFAULT_DB = Path("data/osm_poi.db")

def download_pbf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 100_000_000:
        print(f"PBFは既にあります: {path} ({path.stat().st_size / 1024 / 1024:.1f} MB)")
        return
    print("Geofabrikから関東PBFをダウンロードします。")
    print(PBF_URL)
    with requests.get(PBF_URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        tmp = path.with_suffix(path.suffix + ".part")
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk: continue
                f.write(chunk); done += len(chunk)
                if total:
                    print(f"\r{done/1024/1024:.0f}/{total/1024/1024:.0f} MB ({done/total*100:.1f}%)", end="")
                else:
                    print(f"\r{done/1024/1024:.0f} MB", end="")
        print()
        tmp.replace(path)
    print(f"保存しました: {path}")

def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
    DROP TABLE IF EXISTS poi;
    CREATE TABLE poi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        osm_type TEXT NOT NULL,
        osm_id INTEGER NOT NULL,
        poi_type TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        tags_json TEXT NOT NULL DEFAULT '{}',
        UNIQUE(osm_type, osm_id, poi_type)
    );
    CREATE INDEX idx_poi_type_lat_lon ON poi(poi_type, lat, lon);
    """)
    return conn

def classify(tags):
    if tags.get("highway") == "street_lamp" or tags.get("man_made") == "street_lamp":
        return "street_lamp"
    if tags.get("shop") == "convenience":
        return "convenience"
    if tags.get("amenity") == "police" or "police" in tags:
        return "police"
    return None

class POIHandler(osmium.SimpleHandler):
    def __init__(self, conn):
        super().__init__(); self.conn=conn; self.rows=[]; self.seen=set()
        self.counts={"street_lamp":0,"convenience":0,"police":0}
    def _queue(self, osm_type, osm_id, poi_type, lat, lon, tags):
        key=(osm_type,int(osm_id),poi_type)
        if key in self.seen: return
        self.seen.add(key)
        keep=("name","name:ja","highway","man_made","shop","amenity","police","opening_hours","operator")
        compact={k:tags[k] for k in keep if k in tags}
        self.rows.append((osm_type,int(osm_id),poi_type,float(lat),float(lon),json.dumps(compact,ensure_ascii=False)))
        self.counts[poi_type]+=1
        if len(self.rows)>=5000: self.flush()
    def flush(self):
        if not self.rows: return
        self.conn.executemany("INSERT OR IGNORE INTO poi (osm_type,osm_id,poi_type,lat,lon,tags_json) VALUES (?,?,?,?,?,?)", self.rows)
        self.conn.commit(); self.rows.clear()
    def node(self,n):
        t=classify(n.tags)
        if t and n.location.valid(): self._queue("node",n.id,t,n.location.lat,n.location.lon,n.tags)
    def way(self,w):
        t=classify(w.tags)
        if t not in ("convenience","police"): return
        coords=[]
        for nd in w.nodes:
            try:
                if nd.location.valid(): coords.append((nd.location.lat, nd.location.lon))
            except Exception: pass
        if not coords: return
        lat=sum(x for x,_ in coords)/len(coords); lon=sum(y for _,y in coords)/len(coords)
        self._queue("way",w.id,t,lat,lon,w.tags)

def build_db(pbf_path: Path, db_path: Path) -> None:
    if not pbf_path.exists():
        raise FileNotFoundError(f"{pbf_path} がありません。--download を付けて実行してください。")
    print(f"PBFをローカル解析します: {pbf_path}")
    print("Overpass APIにはアクセスしません。")
    conn=init_db(db_path)
    try:
        h=POIHandler(conn)
        h.apply_file(str(pbf_path), locations=True)
        h.flush()
        print("抽出完了:", h.counts)
    finally:
        conn.close()
    print(f"SQLite保存先: {db_path}")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pbf", default=str(DEFAULT_PBF))
    p.add_argument("--db", default=str(DEFAULT_DB))
    p.add_argument("--download", action="store_true")
    a=p.parse_args(); pbf=Path(a.pbf); db=Path(a.db)
    if a.download: download_pbf(pbf)
    build_db(pbf,db)

if __name__ == "__main__": main()
