from __future__ import annotations
from typing import Optional, Tuple
from pathlib import Path
import sqlite3
import time

class DB:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, isolation_level = None)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self):
        schema_path = Path(__file__).with_name("schema.sql")
        sql = schema_path.read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def upsert_file(self, path:str, mtime: float, size: int) -> int:
        now = time.time()
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO files(path, last_mtime, last_size, last_seen)
            VALUES(?,?,?,?)
            ON CONFLICT(path) DO UPDATE SET
            last_mtime=excluded.last_mtime,
            last_size=excluded.last_size,
            last_seen=excluded.last_seen""",
            (path, mtime, size, now)
        )
        cur.execute(
            """
            SELECT id 
            FROM files 
            WHERE path=?
            """,
            (path,)
        )
        return int(cur.fetchone()[0])
    
    def get_file_state(self, path:str) -> Tuple[int, int, float, int]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, last_offset, last_mtime, last_size
            FROM files
            WHERE ruta=?
            """,
            (path)
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"File not registered in DB: {path}")
        return int(row[0]), int(row[1]), float(row[2]), int(row[3])
    
    def update_file_offset(self, file_id: int, last_offset: int) -> None:
        cur= self.conn.cursor()
        cur.execute(
            """
            UPDATE files 
            SET last_offset=?
            WHERE id=?
            """,
            (last_offset, file_id)
        )
    
    def insert_hand_raw(self, file_id:int, hand_no: Optional[str], raw_hand: str) -> bool:
        now = time.time()
        try:
            self.conn.execute(
                """
                INSERT INTO hands(file_id, hand_no, inserted_at, raw_hand)
                VALUES (?, ?, ?, ?)
                """,
                (file_id, hand_no, now, raw_hand),
            )
            return True
        except sqlite3.IntegrityError:
            # ya existía (PRIMARY KEY)
            return False
    def count_hands(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT 
            count(*)
            FROM hands
            """
        )
        return int(cur.fetchone()[0]) 
