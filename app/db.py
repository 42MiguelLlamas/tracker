import sqlite3
from pathlib import Path

class DB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def _init_schema(self):
        schema_path = Path(__file__).with_name("schema.sql")
        sql = schema_path.read_text(encoding="utf-8")
        self.conn.executescript(sql)
        self.conn.commit()

    def hands_count(self) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM hands")
        return int(cur.fetchone()[0])
    
    def insert_hand(self, hand_id: str, raw_text: str) -> bool:
        try:
            self.conn.execute(
                "INSERT INTO hands(hand_id, raw_text) VALUES (?, ?)",
                (hand_id, raw_text),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # ya existía (PRIMARY KEY)
            return False
    def list_tables(self) -> list[str]:
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        return [r[0] for r in cur.fetchall()]
