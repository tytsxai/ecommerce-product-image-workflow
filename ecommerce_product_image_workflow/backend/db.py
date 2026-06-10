from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS batches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id INTEGER NOT NULL,
  product_id TEXT NOT NULL,
  product_name_en TEXT NOT NULL,
  style_pack TEXT NOT NULL,
  output_set TEXT NOT NULL DEFAULT 'minimum',
  units TEXT NOT NULL DEFAULT 'cm',
  dimensions_json TEXT NOT NULL DEFAULT '{}',
  specs_json TEXT NOT NULL DEFAULT '[]',
  steps_json TEXT NOT NULL DEFAULT '[]',
  tips_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(batch_id) REFERENCES batches(id)
);

CREATE TABLE IF NOT EXISTS source_images (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_pk INTEGER NOT NULL,
  filename TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(product_pk) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS provider_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider_id TEXT NOT NULL,
  display_name TEXT NOT NULL,
  model TEXT NOT NULL,
  config_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generation_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id INTEGER NOT NULL,
  product_pk INTEGER NOT NULL,
  category TEXT NOT NULL,
  slot INTEGER NOT NULL,
  status TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt TEXT NOT NULL,
  config_json TEXT NOT NULL DEFAULT '{}',
  error TEXT,
  asset_id INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(batch_id) REFERENCES batches(id),
  FOREIGN KEY(product_pk) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS generated_assets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER NOT NULL,
  batch_id INTEGER NOT NULL,
  product_pk INTEGER NOT NULL,
  category TEXT NOT NULL,
  filename TEXT NOT NULL,
  path TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  provider_id TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt TEXT NOT NULL,
  response_summary_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(job_id) REFERENCES generation_jobs(id)
);

CREATE TABLE IF NOT EXISTS qa_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset_id INTEGER NOT NULL,
  decision TEXT NOT NULL,
  reject_tag TEXT,
  reviewer TEXT,
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(asset_id) REFERENCES generated_assets(id)
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init(self) -> None:
        with closing(self.connect()) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with closing(self.connect()) as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return int(cur.lastrowid)

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with closing(self.connect()) as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def query_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with closing(self.connect()) as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
