from __future__ import annotations
from typing import Optional, Tuple, Iterable, Any
from pathlib import Path
import sqlite3
import time

class DB:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, isolation_level = None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL;")
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
        row = cur.execute(
            """
            SELECT id 
            FROM files 
            WHERE path=?
            """,
            (path,)
        )
        return int(row["id"])
    
    def get_file_state(self, path:str) -> Tuple[int | None, int, float, int]:
        cur = self.conn.cursor()
        row = cur.execute(
            """
            SELECT id, last_offset, last_mtime, last_size
            FROM files
            WHERE path=?
            """,
            (path,)
        )
        row = cur.fetchone()
        if not row:
            return (None, 0, 0.0, 0)
        return (int(row["id"]), int(row["last_offset"]), float(row["last_mtime"]), int(row["last_size"]))
    
    def set_file_offset(self, file_id: int, last_offset: int, mtime: float, size: int) -> None:
        now = time.time()
        cur= self.conn.cursor()
        cur.execute(
            """
            UPDATE files 
            SET last_offset=?, mtime=?, size=?
            WHERE id=?
            """,
            (last_offset, mtime, size, now, file_id)
        )
        self.conn.commit()

    def _upsert_players(self, names: Iterable[str]) -> None:
        self.conn.executemany(
            "INSERT OR IGNORE INTO players(player_name) VALUES(?)",
            [(n,) for n in names if n]
        )
    
    def insert_hand(self, file_id:int, hand: Any) -> int | None:
        hand_no = getattr(hand, "hand_no", None)
        if not hand_no:
            raise ValueError("insert_hand: hand_no vacio")
        kind = "tournament" if getattr(hand, "tournament_id", None) else "cash"

        with self.conn:
            cur=self.conn.execute(
                """
                INSERT OR IGNORE INTO hands(
                    file_id, hand_no, kind, tournament, stakes, buyin_text, currency, 
                    btn_pos, table_max_seats, local_dt, local_tz, inserted_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    file_id,
                    str(hand_no),
                    int(hand.tournament_id) if getattr(hand, "tournament_id", None) else None,
                    getattr(hand, "stakes", None),
                    getattr(hand, "buy_in", None),
                    getattr(hand, "cur", None),
                    getattr(hand, "button_pos", None),
                    getattr(hand, "table_max_seats", None),
                    getattr(hand, "local_dt", None),
                    getattr(hand, "local_tz", None),
                    time.time(),
                ),
            )
            if cur.rowcount == 0:
                return None
            row = self.conn.execute("SELECT id FROM hands WHERE hand_no=?",(str(hand_no),)).fetchone()
            hand_id = int[row["id"]]

            names: set[str] = set()
            for s in getattr(hand, "seats", []):
                names.add(s.get("player_name", ""))

            #Seats
            self.conn.executemany("""
                INSERT OR REPLACE INTO seats(hand_id,pos,player_name,chips,sitting_out)
                VALUES(?,?,?,?,?)
                """,
                [
                    (
                        hand_id,
                        int(s["pos"]),
                        s["player_name"],
                        str(s["chips"]),
                        int(bool(s.get("sitting_out", 0))),
                    )
                    for s in getattr(hand, "seats", [])
                ],  
            )
            #Posts
            self.conn.executemany("""
                INSERT OR REPLACE INTO posts(hand_id,player_name,kind, amount)
                VALUES(?,?,?,?)
                """,
                [
                    (
                        hand_id,
                        p["player_name"],
                        str(p["kind"]),
                        int(p["amount"]),
                    )
                    for p in getattr(hand, "posts", [])
                ],  
            )
            #Posts
            self.conn.executemany("""
                INSERT OR REPLACE INTO posts(hand_id,player_name,kind, amount)
                VALUES(?,?,?,?)
                """,
                [
                    (
                        hand_id,
                        p["player_name"],
                        str(p["kind"]),
                        int(p["amount"]),
                    )
                    for p in getattr(hand, "posts", [])
                ],  
            )
            #Dealt
            self.conn.executemany("""
                INSERT OR REPLACE INTO dealt(hand_id,player_name,cards)
                VALUES(?,?,?,?)
                """,
                [
                    (
                        hand_id,
                        str(d["player_name"]),
                        str(d["cards"])
                    )
                    for d in getattr(hand, "dealt", [])
                ],  
            )
            #Board
            board = getattr(hand, "board", {}) or {}
            self.conn.execute(
                "INSERT OR REPLACE INTO board(hand_id, flop, turn, river) VALUES(?,?,?,?)",
                (hand_id, board.get("flop"), board.get("turn"), board.get("river")),
            )

            #Actions
            seq = 0
            rows = []
            actions_by_street = getattr(hand, "actions_by_street", {}) or {}
            for street in ("preflop", "flop", "turn", "river", "showdown"):
                for a in actions_by_street.get(street, []):
                    seq += 1
                    rows.append(
                        (
                            hand_id,
                            seq,
                            street,
                            a.get("player_name"),
                            a.get("action"),
                            a.get("amount") or a.get("bet") or a.get("call_amount"),
                            a.get("raise_from"),
                            a.get("raise_to"),
                            1 if a.get("is_all_in") else 0,
                        )
                    )
            if rows:
                self.conn.executemany(
                    """
                    INSERT INTO actions(
                      hand_id, seq, street, player_name, action,
                      amount_text, raise_from_text, raise_to_text, is_allin
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    rows,
                )


    def count_hands(self) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT 
            count(*)
            FROM hands
            """
        )
        return int(cur.fetchone()[0])
