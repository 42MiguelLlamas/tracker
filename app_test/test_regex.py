from __future__ import annotations
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, List
import re

from .db import DB

HAND_START_RE = re.compile(rb"""
                           (?m)^(?:\xef\xbb\xbf)?PokerStars\s+Hand\s+\#(?P<hand_id>\d+):\s*
                           (?:
                                Tournament\s+\#(?P<tournament_id>\d+),.*?
                                (?P<buy_in>(?:[^\d]+)?\d+(?:\.\d+)?\+(?:[^\d]+)?\d+(?:\.\d+)?)\s+(?P<cur>[A-Z]{3}).*?
                            |
                                .*?\((?P<stakes>(?:[^\d]+)?\d+(?:\.\d+)?/(?:[^\d]+)?\d+(?:\.\d+)?)\s+(?P<cur_cash>[A-Z]{3})\).*?   
                           )
                           \s*-\s*
                           (?P<local_dt>\d{4}/\d{2}/\d{2}\s+\d{1,2}:\d{2}:\d{2})\s+(?P<local_tz>[A-Z]{2,5})
                           """, 
                           re.VERBOSE)

TABLE_START_RE = re.compile(rb"""
                            (?m)^Table\s+'.*?'\s+(?P<max_seats>\d+)-max\s+Seat\s+\#(?P<btn_pos>\d+)\s+is\s+the\s+button\s*$
                            """, 
                           re.VERBOSE)

SEAT_RE = re.compile(rb"""
                        (?m)^Seat\s+(?P<seat_no>\d+):\s+(?P<player_name>.+?)\s+
                        \((?P<chips>(?:[^\d]+)?\d+(?:\.\d+)?)\s+in\s+chips\)
                        (?:\s+(?:is\s+sitting\s+out|out\s+of\s+hand\s+\(.*?\)))?\s*$
                     """, 
                    re.VERBOSE)

POST_RE = re.compile(rb"""
                        (?m)^(?P<player_name>.+?):\s+posts\s+(?P<kind>the\s+ante|small\s+blind|big\s+blind).+?(?P<amount>\d+(?:\.\d+)?)\s*$
                     """, 
                    re.VERBOSE)

PREFLOP_RE = re.compile(rb"""
                        (?m)^\*\*\*\s+HOLE\s+CARDS\s+\*\*\*\s*$
                     """, 
                    re.VERBOSE)

FLOP_RE = re.compile(rb"""
                        (?m)^\*\*\*\s+FLOP\s+\*\*\*\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

TURN_RE = re.compile(rb"""
                        (?m)^\*\*\*\s+TURN\s+\*\*\*\s+\[.+?\]\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

RIVER_RE = re.compile(rb"""
                        (?m)^\*\*\*\s+RIVER\s+\*\*\*\s+\[.+?\]\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

SUMMARY_RE = re.compile(rb"""
                        (?m)^\*\*\*\s+SUMMARY\s+\*\*\*\s*$
                        """, 
                        re.VERBOSE)

DEALT_RE = re.compile(rb"""
                        (?m)^Dealt\s+to\s+(?P<player_name>.+?)\s+\[(?P<cards>.+?)\]\s*$
                     """, 
                    re.VERBOSE)

ACTION_RE = re.compile(rb"""
                        (?m)^(?P<player_name>.+?):\s+
                        (?P<action>folds|checks|bets|raises|calls)
                        (?:
                            \s*$ |
                            \s+(?:[^\d]+)?(?P<bet>\d+(?:\.\d+)?)\s*$ |
                            \s+(?:[^\d]+)?(?P<raise_from>\d+(?:\.\d+)?)\s+to\s+(?:[^\d]+)?(?P<raise_to>\d+(?:\.\d+)?) |
                            \s+(?:[^\d]+)?(?P<call_amount>\d+(?:\.\d+)?) 
                        )
                        (?:\s+(?P<is_all_in>and\s+is\s+all-in))?\s*$
                        """, 
                        re.VERBOSE)


SEAT_SUMMARY_RE = re.compile(rb"""
                        (?m)^Seat\s+\d+:\s+
                        (?P<player_name>.+?)
                        \s+
                        (?:
                            showed\s+\[(?P<showed>.+?)\]
                            (?:\s+and\s+(?:won|lost)(?:\s+\((?P<won>.+?)\))?.*?)?
                        |
                            mucked\s+\[(?P<mucked>.+?)\]
                        |
                            collected\s+\((?P<collected>.+?)\)
                        )
                        \s*$
                        """, re.VERBOSE)



line_cash = """PokerStars Hand #259598453823:  Hold'em No Limit (€0.01/€0.02 EUR) - 2026/02/05 7:09:57 CET [2026/02/05 1:09:57 ET]
Table 'Cyrene' 6-max Seat #4 is the button
Seat 1: NassLaKlass (€1.60 in chips) is sitting out
Seat 5: cabeza_buceo (€2 in chips) is sitting out
Seat 2: Doods31tlse (€2.12 in chips) 
Seat 3: OvalleAstur (€2 in chips) 
Seat 4: sunbreathking (€1.90 in chips) 
Doods31tlse: posts small blind €0.01
OvalleAstur: posts big blind €0.02
*** HOLE CARDS ***
Dealt to sunbreathking [9h 7h]
sunbreathking has timed out
sunbreathking: folds 
Doods31tlse: raises €0.02 to €0.04
OvalleAstur: folds 
Uncalled bet (€0.02) returned to Doods31tlse
Doods31tlse collected €0.04 from pot
margezm joins the table at seat #6 
*** SUMMARY ***
Total pot €0.04 | Rake €0 
Seat 1: NassLaKlass
Seat 5: cabeza_buceo
Seat 2: Doods31tlse (small blind) collected (€0.04)
Seat 3: OvalleAstur (big blind) folded before Flop
Seat 4: sunbreathking (button) folded before Flop (didn't bet)
"""

line_tournament= """
PokerStars Hand #259588938913: Tournament #3970423882, €0.90+€0.10 EUR Hold'em No Limit - Level XII (1000/2000) - 2026/02/04 16:40:28 CET [2026/02/04 10:40:28 ET]
Table '3970423882 13' 8-max Seat #8 is the button
Seat 1: 1CAND100 (29715 in chips) 
Seat 2: orquidea71 (33830 in chips) is sitting out
Seat 3: horrorozzo (77652 in chips) 
Seat 4: najas88 (44224 in chips) 
Seat 5: javibetis8 (182200 in chips) 
Seat 6: tonigin78 (18072 in chips) 
Seat 7: Kekasoo (45100 in chips) is sitting out
Seat 8: sunbreathking (98373 in chips) 
1CAND100: posts the ante 200
orquidea71: posts the ante 200
horrorozzo: posts the ante 200
najas88: posts the ante 200
javibetis8: posts the ante 200
tonigin78: posts the ante 200
Kekasoo: posts the ante 200
sunbreathking: posts the ante 200
1CAND100: posts small blind 1000
orquidea71: posts big blind 2000
*** HOLE CARDS ***
Dealt to sunbreathking [8s Kh]
horrorozzo: calls 2000
najas88: folds 
javibetis8: calls 2000
tonigin78: calls 2000
Kekasoo: folds 
sunbreathking: folds 
1CAND100: calls 1000
orquidea71: folds 
*** FLOP *** [6d 8h 9c]
1CAND100: checks 
horrorozzo: bets 2000
javibetis8: calls 2000
tonigin78: calls 2000
1CAND100: folds 
*** TURN *** [6d 8h 9c] [7h]
horrorozzo: bets 2000
javibetis8: calls 2000
tonigin78: calls 2000
*** RIVER *** [6d 8h 9c 7h] [7c]
horrorozzo: bets 4000
javibetis8: raises 4000 to 8000
tonigin78: folds 
horrorozzo: calls 4000
*** SHOW DOWN ***
javibetis8: shows [Tc Qs] (a straight, Six to Ten)
horrorozzo: mucks hand 
javibetis8 collected 39600 from pot
*** SUMMARY ***
Total pot 39600 | Rake 0 
Board [6d 8h 9c 7h 7c]
Seat 1: 1CAND100 (small blind) folded on the Flop
Seat 2: orquidea71 (big blind) folded before Flop
Seat 3: horrorozzo mucked [3c 5d]
Seat 4: najas88 folded before Flop (didn't bet)
Seat 5: javibetis8 showed [Tc Qs] and won (39600) with a straight, Six to Ten
Seat 6: tonigin78 folded on the River
Seat 7: Kekasoo folded before Flop (didn't bet)
Seat 8: sunbreathking (button) folded before Flop (didn't bet)
"""

def test_table(line: str):
    b = line.encode("utf-8")   # convertir a bytes
    m = TABLE_START_RE.search(b)
    if m:
        print({k: v.decode("utf-8", "ignore") for k, v in m.groupdict().items() if v is not None})
    else:
        print("NO MATCH")

def test_hand_start(line: str):
    first = line.splitlines()[0]
    b = first.encode("utf-8")
    m = HAND_START_RE.match(b)
    if m:
        print({k: v.decode("utf-8", "ignore") for k, v in m.groupdict().items() if v is not None})
    else:
        print("NO MATCH")

def test_seat(block: str):
    b = block.encode("utf-8")
    for m in SEAT_RE.finditer(b):
        print({k: v.decode("utf-8", "ignore") for k, v in m.groupdict().items() if v is not None})

def test_post(block: str):
    b = block.encode("utf-8")
    for m in POST_RE.finditer(b):
        print({k: v.decode("utf-8", "ignore") for k, v in m.groupdict().items() if v is not None})


def dump_regex_matches(data: bytes | str, patterns: list[tuple[str, re.Pattern[bytes]]], *, show_line: bool = True) -> None:
    """
    Recorre `data` (bytes o str), ejecuta cada regex bytes-pattern con finditer,
    e imprime cada match con groups para debug.
    """
    if isinstance(data, str):
        b = data.encode("utf-8", "replace")
    else:
        b = data

    def _safe_decode(x: bytes | None) -> str | None:
        if x is None:
            return None
        return x.decode("utf-8", "replace")

    print(f"DATA: {len(b)} bytes\n")

    for name, cre in patterns:
        matches = list(cre.finditer(b))
        print(f"=== {name} ===  matches: {len(matches)}")
        if not matches:
            print()
            continue

        for i, m in enumerate(matches, 1):
            s, e = m.span()
            gd = {k: _safe_decode(v) for k, v in (m.groupdict() or {}).items() if v is not None}

            # texto exacto del match (para ver qué capturó)
            matched_text = b[s:e].decode("utf-8", "replace")

            print(f"[{i}] span=({s},{e})")
            if gd:
                print("  groupdict:", gd)

            if show_line:
                # Para debug: imprime el match "tal cual"
                print("  match:")
                print("  " + matched_text.replace("\n", "\n  ").rstrip())
            print()

        print()


def main():
    patterns = [
        ("HAND_START_RE", HAND_START_RE),
        ("TABLE_START_RE", TABLE_START_RE),
        ("SEAT_RE", SEAT_RE),
        ("POST_RE", POST_RE),
        ("PREFLOP_RE", PREFLOP_RE),
        ("DEALT_RE", DEALT_RE),
        ("ACTION_RE", ACTION_RE),
        ("FLOP_RE", FLOP_RE),
        ("TURN_RE", TURN_RE),
        ("RIVER_RE", RIVER_RE),
        ("SUMMARY_RE", SUMMARY_RE),
        ("SEAT_SUMMARY_RE", SEAT_SUMMARY_RE),
    ]

    print("---- TOURNAMENT ----")
    dump_regex_matches(line_tournament, patterns)

    print("---- CASH ----")
    dump_regex_matches(line_cash, patterns)


if __name__ == "__main__":
    main()

