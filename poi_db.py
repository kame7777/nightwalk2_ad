from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path("data/osm_poi.db")


def connect(db_path: str | Path = DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(db_path: str | Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS poi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poi_type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            tags_json TEXT NOT NULL DEFAULT '{}',
            UNIQUE(poi_type, lat, lon)
        );

        CREATE INDEX IF NOT EXISTS idx_poi_type_lat_lon
        ON poi(poi_type, lat, lon);
        """)


def replace_pois(poi_type: str, rows: Iterable[tuple[float, float, dict]], db_path=DB_PATH) -> int:
    rows = list(rows)
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute("DELETE FROM poi WHERE poi_type = ?", (poi_type,))
        conn.executemany(
            "INSERT OR IGNORE INTO poi (poi_type, lat, lon, tags_json) VALUES (?, ?, ?, ?)",
            [(poi_type, float(lat), float(lon), json.dumps(tags or {}, ensure_ascii=False))
             for lat, lon, tags in rows]
        )
    return len(rows)


def count_pois(db_path=DB_PATH) -> dict[str, int]:
    init_db(db_path)
    with connect(db_path) as conn:
        return dict(conn.execute(
            "SELECT poi_type, COUNT(*) FROM poi GROUP BY poi_type"
        ).fetchall())


def query_bbox(south: float, west: float, north: float, east: float,
               poi_type: str | None = None, db_path=DB_PATH):
    """Return only POIs inside the requested bbox. This is the hot path used by the app."""
    init_db(db_path)
    sql = """
        SELECT lat, lon, tags_json
        FROM poi
        WHERE lat BETWEEN ? AND ?
          AND lon BETWEEN ? AND ?
    """
    params: list = [south, north, west, east]
    if poi_type:
        sql += " AND poi_type = ?"
        params.append(poi_type)

    with connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    return [(lat, lon, json.loads(tags)) for lat, lon, tags in rows]
