from __future__ import annotations

from typing import Dict, Optional, Set, List
from .classes import *
from .regex import *
from .parse_stats import parse_stats
from .parse_position import parse_position


def to_float_money(b: bytes | None) -> float | None:
    if b is None:
        return None
    s = b.decode("utf-8", "replace").strip()
    s = s.replace("€", "").replace("$", "").replace("\xa0", " ").strip()
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_hand(lines: List[bytes]) -> HandData:
    #Paso 1. Header Line
    hand = HandData(
        hand_id=None, tournament_id=None, buy_in=None, stakes=None,
        cur=None, local_dt=None, local_tz=None, max_seats=None, players_seated=None, button_pos=None
    )
    if not lines:
        return hand
    m = HAND_START_RE.match(lines[0])
    if not m:
        print("Hand Start line NO MATCH:", line)
        return None
    gd = m.groupdict()
    hand.hand_id = gd["hand_id"].decode("utf-8", "replace")
    hand.tournament_id = (gd.get("tournament_id") or b"").decode("utf-8", "replace") or None
    hand.buy_in = (gd.get("buy_in") or b"").decode("utf-8", "replace") or None
    hand.stakes = (gd.get("stakes") or b"").decode("utf-8", "replace") or None
    hand.cur = (gd.get("cur") or gd.get("cur_cash") or b"").decode("utf-8", "replace") or None
    hand.local_dt = gd["local_dt"].decode("utf-8", "replace")
    hand.local_tz = gd["local_tz"].decode("utf-8", "replace")
    #Paso 2. Table Line
    mt = TABLE_START_RE.match(lines[1])
    if not mt:
        print("Table line NO MATCH:", line)
        return None

    tgd = mt.groupdict()
    hand.max_seats = int(tgd["max_seats"].decode("utf-8", "replace"))
    hand.button_pos = int(tgd["btn_pos"].decode("utf-8", "replace"))

    #Paso 3. Sitios, posts, resultados.
    current_street = "preflop"
    in_summary = False
    for line in lines:
        if line.startswith(b"*** FLOP"):
            current_street = "flop"
        elif line.startswith(b"*** TURN"):
            current_street = "turn"
        elif line.startswith(b"*** RIVER"):
            current_street = "river"

        if line.startswith(b"*** SUMMARY"):
            in_summary = True
            continue
        if current_street == "preflop" and line.startswith(b"Dealt to"):
            mdealt = DEALT_RE.match(line)
            if not mdealt:
                continue
            dealt_group = mdealt.groupdict()
            hand.cards = dealt_group.get("cards")
        if line.startswith(b"Seat "):
            if in_summary == False:
                ms = SEAT_RE.match(line)
                if not ms:
                    continue
                sgd = ms.groupdict()
                bounty = None
                if sgd.get("bounty") is not None:
                    bounty = to_float_money(sgd["bounty"])
                seat = Seat(
                    pos=sgd["seat_no"].decode("utf-8", "replace"),          # o int(...)
                    player_name=sgd["player_name"].decode("utf-8", "replace"),
                    chips=to_float_money(sgd["chips"]),
                    bounty=bounty,
                    sitting_out=(b"is sitting out" in line or b"out of hand" in line),
                )
                hand.seats.append(seat)
                continue
            else:
                msu = SEAT_SUMMARY_RE.match(line.rstrip(b"\r\n"))
                if not msu:
                    continue
                sgd = msu.groupdict()
                player = sgd["player_name"].decode("utf-8", "replace")

                cards = None
                collected = None

                if sgd.get("showed"):
                    cards = sgd["showed"].decode("utf-8", "replace")
                    if sgd.get("won"):
                        try:
                            collected = to_float_money(sgd["won"])
                        except ValueError:
                            collected = None
                elif sgd.get("mucked"):
                    cards = sgd["mucked"].decode("utf-8", "replace")
                elif sgd.get("collected"):
                    try:
                        collected = to_float_money(sgd["collected"])
                    except ValueError:
                        collected = None

                res = PlayerResult(player_name=player, cards=cards, collected=collected)
                hand.results.append(res)
                continue

        if b": posts " in line:
            mp = POST_RE.match(line)
            if not mp:
                print("POST NO MATCH:", repr(line))
                continue

            pgd = mp.groupdict()
            post = Post(
                player_name=pgd["player_name"].decode("utf-8", "replace"),
                kind=pgd["kind"].decode("utf-8", "replace"),
                amount=to_float_money(pgd["amount"]),
            )
            hand.posts.append(post)
            continue

        if b": " in line and (
            b": folds" in line or
            b": checks" in line or
            b": bets" in line or
            b": raises" in line or
            b": calls" in line
        ):
            ma = ACTION_RE.match(line)
            if not ma:
                #print("ACTION NO MATCH:", repr(line))
                continue
            agd = ma.groupdict()

            amount = None
            raise_from = None
            raise_to = None

            if agd.get("bet"):
                amount = to_float_money(agd["bet"])
            elif agd.get("call_amount"):
                amount = to_float_money(agd["call_amount"])
            elif agd.get("raise_from") or agd.get("raise_to"):
                raise_from = to_float_money(agd["raise_from"])
                raise_to = to_float_money(agd["raise_to"])

            action = Action(
                street=current_street,  # lo pondremos en el siguiente paso
                player_name=agd["player_name"].decode("utf-8", "replace"),
                action=agd["action"].decode("utf-8", "replace"),
                amount=amount,
                raise_from=raise_from,
                raise_to=raise_to,
                is_all_in=agd.get("is_all_in") is not None,
            )

            hand.actions.append(action)
            continue
    hand.players_seated = len(hand.seats)
    parse_position(hand)
    hand.stats = parse_stats(hand)
    return hand
