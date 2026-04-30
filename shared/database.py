import sqlite3
import os
import threading
from typing import Optional, List, Tuple

_local = threading.local()


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    def get_conn(self) -> sqlite3.Connection:
        if not hasattr(_local, "conn") or _local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            _local.conn = conn
        return _local.conn

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        return self.get_conn().execute(sql, params)

    def executemany(self, sql: str, params_list: List[Tuple]) -> sqlite3.Cursor:
        return self.get_conn().executemany(sql, params_list)

    def commit(self):
        self.get_conn().commit()

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[dict]:
        row = self.execute(sql, params).fetchone()
        return dict(row) if row else None

    def fetchall(self, sql: str, params: Tuple = ()) -> List[dict]:
        rows = self.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def init_tables(self, sql_path: Optional[str] = None):
        if sql_path and os.path.exists(sql_path):
            with open(sql_path, "r", encoding="utf-8") as f:
                self.get_conn().executescript(f.read())
            self.commit()
        else:
            self._create_default_tables()
            self.commit()

    def _create_default_tables(self):
        self.get_conn().executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                author TEXT DEFAULT '',
                source_text_path TEXT DEFAULT '',
                split_mode TEXT DEFAULT 'auto',
                style_hint TEXT DEFAULT '',
                status TEXT DEFAULT 'created',
                total_segments INTEGER DEFAULT 0,
                completed_segments INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS segments (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                segment_index INTEGER NOT NULL,
                title TEXT DEFAULT '',
                content TEXT DEFAULT '',
                summary TEXT DEFAULT '',
                status TEXT DEFAULT 'saved',
                total_shots INTEGER DEFAULT 0,
                rendered_shots INTEGER DEFAULT 0,
                failed_shots INTEGER DEFAULT 0,
                pending_recompose INTEGER DEFAULT 0,
                last_modified_field TEXT DEFAULT '',
                video_path TEXT DEFAULT '',
                video_duration REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS shots (
                id TEXT PRIMARY KEY,
                segment_id TEXT NOT NULL,
                shot_index INTEGER NOT NULL,
                scene_description TEXT DEFAULT '',
                prompt TEXT DEFAULT '',
                negative_prompt TEXT DEFAULT 'blurry, low quality, distorted, deformed',
                dialogue TEXT DEFAULT '',
                narrator_text TEXT DEFAULT '',
                speaker TEXT DEFAULT '',
                camera TEXT DEFAULT '',
                characters_json TEXT DEFAULT '[]',
                duration_hint REAL DEFAULT 5.0,
                image_path TEXT DEFAULT '',
                audio_path TEXT DEFAULT '',
                audio_duration REAL DEFAULT 0,
                quality_score REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                error_message TEXT DEFAULT '',
                retry_count INTEGER DEFAULT 0,
                current_version INTEGER DEFAULT 1,
                is_current INTEGER DEFAULT 1,
                superseded_by TEXT DEFAULT '',
                supersedes TEXT DEFAULT '',
                audio_source TEXT DEFAULT 'generated',
                image_source TEXT DEFAULT 'generated',
                pending_image_regen INTEGER DEFAULT 0,
                pending_audio_regen INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (segment_id) REFERENCES segments(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS shot_versions (
                id TEXT PRIMARY KEY,
                shot_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                image_path TEXT DEFAULT '',
                prompt TEXT DEFAULT '',
                negative_prompt TEXT DEFAULT '',
                source TEXT DEFAULT 'generated',
                created_at TEXT NOT NULL,
                FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_segments_project ON segments(project_id);
            CREATE INDEX IF NOT EXISTS idx_shots_segment ON shots(segment_id);
            CREATE INDEX IF NOT EXISTS idx_shots_status ON shots(status);
            CREATE INDEX IF NOT EXISTS idx_shot_versions_shot ON shot_versions(shot_id);
        """)


_db_instance: Optional[Database] = None


def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        from shared.config import get_config
        cfg = get_config()
        db_path = cfg["database"]["sqlite_path"]
        _db_instance = Database(db_path)
    return _db_instance