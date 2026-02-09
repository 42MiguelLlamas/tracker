from __future__ import annotations
from typing import Optional, Tuple, Iterable, Any, Dict
from pathlib import Path
import sqlite3
import time
from datetime import datetime, timezone, timedelta

CET = timezone(timedelta(hours=1))

def parse_hand_ts(local_dt: str) -> int:
    dt_naive = datetime.strptime(local_dt, "%Y/%m/%d %H:%M:%S")
    dt = dt_naive.replace(tzinfo=CET)
    return int(dt.timestamp())


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


    def print_query(self, query: str, params: tuple = ()):
        cur = self.conn.cursor()
        cur.execute(query, params)

        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        if not rows:
            print("No rows returned.")
            return

        # ancho de columnas dinámico
        col_widths = [len(c) for c in cols]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        # header
        header = " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols))
        sep = "-+-".join("-" * w for w in col_widths)

        print(header)
        print(sep)

        # filas
        for row in rows:
            print(" | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)))
            
    def run_sql_file(self, path, params=()):
        with open(path, "r", encoding="utf-8") as f:
            query = f.read()
        self.print_query(query, params)

    def upsert_file(self, path:str, mtime: float, size: int) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO files(path, last_mtime, last_size)
            VALUES(?,?,?)
            ON CONFLICT(path) DO UPDATE SET
            last_mtime=excluded.last_mtime,
            last_size=excluded.last_size
            """,
            (path, mtime, size),
        )
    
    def get_file_state(self, path:str) -> Tuple:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, last_offset
            FROM files
            WHERE path=?
            """,
            (path,)
        )
        row = cur.fetchone()
        if not row:
            return 0
        return (int(row["id"]), int(row["last_offset"]))
    
    def set_file_offset(self, file_id: int, last_offset: int, mtime: float, size: int) -> None:
        cur= self.conn.cursor()
        cur.execute(
            """
            UPDATE files 
            SET last_offset=?, last_mtime=?, last_size=?
            WHERE id=?
            """,
            (last_offset, mtime, size, file_id)
        )
        self.conn.commit()

    def get_player_id(self, player_name: str) -> int:
        """
        Devuelve el player_id asociado al player_name.
        Si no existe, lo crea.
        """
        cur = self.conn.cursor()

        # 1. Intentar obtenerlo
        cur.execute(
            "SELECT player_id FROM players WHERE player_name = ?",
            (player_name,)
        )
        row = cur.fetchone()
        if row:
            return row[0]

        # 2. No existe → insertarlo
        cur.execute(
            "INSERT INTO players(player_name) VALUES (?)",
            (player_name,)
        )
        self.conn.commit()

        return cur.lastrowid
    
    def insert_hand(self, file_id:int, hand: Any) -> int | None:
        hand_no = getattr(hand, "hand_id", None)
        if not hand_no:
            raise ValueError("insert_hand: hand_no vacio")
        kind = "tournament" if getattr(hand, "tournament_id", None) else "cash"
        #print("Insertando mano.")
        with self.conn:
            cur=self.conn.execute(
                """
                INSERT OR IGNORE INTO hands(
                    file_id, hand_no, kind, tournament_id, stakes, buyin, currency, 
                    btn_pos, max_seats, players_seated, hand_ts, inserted_at
                )
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    file_id,
                    str(hand_no),
                    kind,
                    int(hand.tournament_id) if getattr(hand, "tournament_id", None) else None,
                    getattr(hand, "stakes", None),
                    getattr(hand, "buy_in", None),
                    getattr(hand, "cur", None),
                    getattr(hand, "button_pos", None),
                    getattr(hand, "max_seats", None),
                    getattr(hand, "players_seated", None),
                    parse_hand_ts(getattr(hand, "local_dt", None)),
                    time.time(),
                ),
            )
            if cur.rowcount == 0:
                return None
            row = self.conn.execute("SELECT id FROM hands WHERE hand_no=?",(str(hand_no),)).fetchone()
            hand_id = int(row["id"])

            players_dict = {}
            for s in hand.seats:
                player_name = str(s.player_name)
                player_id = self.get_player_id(player_name)
                players_dict[player_name] = player_id

            #Seats
            self.conn.executemany("""
                INSERT OR REPLACE INTO seats(hand_id,pos,player_id,chips,sitting_out)
                VALUES(?,?,?,?,?)
                """,
                [
                    (
                        hand_id,
                        int(s.pos),
                        players_dict[s.player_name],
                        str(s.chips),
                        int(bool(s.sitting_out)),
                    )
                    for s in getattr(hand, "seats", [])
                ],  
            )
            #Posts
            self.conn.executemany("""
                INSERT OR REPLACE INTO posts(hand_id,player_id,kind, amount)
                VALUES(?,?,?,?)
                """,
                [
                    (
                        hand_id,
                        players_dict[p.player_name],
                        str(p.kind),
                        int(p.amount),
                    )
                    for p in getattr(hand, "posts", [])
                ],  
            )

            #Dealt
            # self.conn.executemany("""
            #     INSERT OR REPLACE INTO dealt(hand_id,player_id,cards)
            #     VALUES(?,?,?,?)
            #     """,
            #     [
            #         (
            #             hand_id,
            #             players_dict[str(d.player_name)],
            #             str(d.cards)
            #         )
            #         for d in getattr(hand, "dealt", [])
            #     ],  
            # )
            #Board
            # board = getattr(hand, "board", {}) or {}
            # self.conn.execute(
            #     "INSERT OR REPLACE INTO board(hand_id, flop, turn, river) VALUES(?,?,?,?)",
            #     (hand_id, board.get("flop"), board.get("turn"), board.get("river")),
            # )

            #Actions
            def _street_to_int(street: str | None) -> int:
                s = (street or "").strip().lower()
                return {"preflop": 0, "flop": 1, "turn": 2, "river": 3, "showdown": 4}.get(s, 0)

            def _action_to_int(action: str | None) -> int:
                a = (action or "").strip().lower()
                return {
                    "folds": 0, "checks": 1, "calls": 2, "bets": 3, "raises": 4,
                    "fold": 0,  "check": 1,  "call": 2,  "bet": 3,  "raise": 4,
                }.get(a, -1)


            # -------- Actions (FIX) --------
            seq = 0
            rows = []

            for a in (hand.actions or []):
                if not a.player_name:
                    continue

                pid = players_dict.get(a.player_name)
                if pid is None:
                    pid = self.get_player_id(a.player_name)
                    players_dict[a.player_name] = pid

                seq += 1
                rows.append(
                    (
                        hand_id,
                        seq,
                        _street_to_int(a.street),
                        pid,
                        _action_to_int(a.action),
                        int(a.amount) if a.amount is not None else None,
                        int(a.raise_from) if a.raise_from is not None else None,
                        int(a.raise_to) if a.raise_to is not None else None,
                        1 if a.is_all_in else 0,
                    )
                )

            if rows:
                self.conn.executemany(
                    """
                    INSERT INTO actions(
                    hand_id, seq, street, player_id, action,
                    amount, raise_from, raise_to, is_allin
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    rows,
                )
            
            for player, stat in hand.stats.items():
                self.db_update_player_stats(players_dict[player], stat)


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
    
    def db_update_player_stats(self, player, st) -> None:
        """
        Inserta o acumula stats de hand.stats en la tabla player_stats
        """

        sql = """
        INSERT INTO player_stats (
            player_id, pos, max_seats, players_seated, stack_bb_bucket,
            hands,
            rfi, rfi_opp, vpip, pfr,
            threebet, threebet_opp,
            fold_to_3bet, fold_to_3bet_opp,
            fourbet, fourbet_opp,
            squeeze, squeeze_opp,
            steal, steal_opp,
            fold_bb_vs_steal, fold_bb_vs_steal_opp,

            saw_flop,
            cbet_flop, cbet_flop_opp,
            fold_to_cbet_flop, fold_to_cbet_flop_opp,
            check_raise_flop, check_raise_flop_opp,
            donk_flop, donk_flop_opp,

            saw_turn,
            barrel_turn, barrel_turn_opp,
            fold_to_barrel_turn, fold_to_barrel_turn_opp,

            saw_river,
            barrel_river, barrel_river_opp,
            fold_to_barrel_river, fold_to_barrel_river_opp,
            river_bet, river_bet_opp,

            went_showdown, won_showdown
        )
        VALUES (?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,
                ?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?,?,?,?,
                ?,?,?,?,?,
                ?,?,?,?,?,?,
                ?,?)
        ON CONFLICT(player_id, pos, players_seated, stack_bb_bucket)
        DO UPDATE SET
            hands = hands + excluded.hands,

            rfi = rfi + excluded.rfi,
            rfi_opp = rfi_opp + excluded.rfi_opp,
            vpip = vpip + excluded.vpip,
            pfr = pfr + excluded.pfr,

            threebet = threebet + excluded.threebet,
            threebet_opp = threebet_opp + excluded.threebet_opp,

            fold_to_3bet = fold_to_3bet + excluded.fold_to_3bet,
            fold_to_3bet_opp = fold_to_3bet_opp + excluded.fold_to_3bet_opp,

            fourbet = fourbet + excluded.fourbet,
            fourbet_opp = fourbet_opp + excluded.fourbet_opp,

            squeeze = squeeze + excluded.squeeze,
            squeeze_opp = squeeze_opp + excluded.squeeze_opp,

            steal = steal + excluded.steal,
            steal_opp = steal_opp + excluded.steal_opp,

            fold_bb_vs_steal = fold_bb_vs_steal + excluded.fold_bb_vs_steal,
            fold_bb_vs_steal_opp = fold_bb_vs_steal_opp + excluded.fold_bb_vs_steal_opp,

            saw_flop = saw_flop + excluded.saw_flop,

            cbet_flop = cbet_flop + excluded.cbet_flop,
            cbet_flop_opp = cbet_flop_opp + excluded.cbet_flop_opp,

            fold_to_cbet_flop = fold_to_cbet_flop + excluded.fold_to_cbet_flop,
            fold_to_cbet_flop_opp = fold_to_cbet_flop_opp + excluded.fold_to_cbet_flop_opp,

            check_raise_flop = check_raise_flop + excluded.check_raise_flop,
            check_raise_flop_opp = check_raise_flop_opp + excluded.check_raise_flop_opp,

            donk_flop = donk_flop + excluded.donk_flop,
            donk_flop_opp = donk_flop_opp + excluded.donk_flop_opp,

            saw_turn = saw_turn + excluded.saw_turn,

            barrel_turn = barrel_turn + excluded.barrel_turn,
            barrel_turn_opp = barrel_turn_opp + excluded.barrel_turn_opp,

            fold_to_barrel_turn = fold_to_barrel_turn + excluded.fold_to_barrel_turn,
            fold_to_barrel_turn_opp = fold_to_barrel_turn_opp + excluded.fold_to_barrel_turn_opp,

            saw_river = saw_river + excluded.saw_river,

            barrel_river = barrel_river + excluded.barrel_river,
            barrel_river_opp = barrel_river_opp + excluded.barrel_river_opp,

            fold_to_barrel_river = fold_to_barrel_river + excluded.fold_to_barrel_river,
            fold_to_barrel_river_opp = fold_to_barrel_river_opp + excluded.fold_to_barrel_river_opp,

            river_bet = river_bet + excluded.river_bet,
            river_bet_opp = river_bet_opp + excluded.river_bet_opp,

            went_showdown = went_showdown + excluded.went_showdown,
            won_showdown = won_showdown + excluded.won_showdown
        ;
        """

        cur = self.conn.cursor()


        vpip = (st.cold_call or 0) + (st.rfi or 0)
        pfr = st.rfi or 0

        cur.execute(sql, (
            player,
            st.position,
            st.max_seats,
            st.players_at_table,
            st.stack_bucket,

            st.hands,

            st.rfi, st.rfi_opp, vpip, pfr,

            st.three_bet, st.three_bet_opp,
            st.fold_to_3bet, st.fold_to_3bet_opp,
            st.four_bet, st.four_bet_opp,
            st.squeeze, st.squeeze_opp,
            st.steal, st.steal_opp,
            st.foldbb_vs_steal, st.foldbb_vs_steal_opp,

            st.saw_flop,
            st.c_bet, st.c_bet_opp,
            st.fold_to_cbet, st.fold_to_cbet_opp,
            st.check_raise_flop, st.check_raise_flop_opp,
            st.donk_flop, st.donk_flop_opp,

            st.saw_turn,
            st.barrel_turn, st.barrel_turn_opp,
            st.fold_to_barrel_turn, st.fold_to_barrel_turn_opp,

            st.saw_river,
            st.barrel_river, st.barrel_river_opp,
            st.fold_to_barrel_river, st.fold_to_barrel_river_opp,
            st.river_bet, st.river_bet_opp,

            st.went_showdown, st.won_showdown
        ))

        self.conn.commit()
