from __future__ import annotations

from typing import Dict, Optional, Set, List
from .classes import *


def _is_steal_pos(label: Optional[str]) -> bool:
    if not label:
        return False
    x = label.strip().upper()
    return x in {"CO", "BTN"}


def _parse_bb_from_stakes(stakes: Optional[str]) -> Optional[float]:
    if not stakes:
        return None
    s = stakes.strip().replace(" ", "")
    for sep in ("/", "-", ":"):
        if sep in s:
            parts = s.split(sep)
            if len(parts) >= 2:
                try:
                    return float(parts[1])
                except ValueError:
                    return None
    return None


def _stack_bucket(chips: Optional[float], bb: Optional[float]) -> Optional[int]:
    if chips is None or bb is None or bb <= 0:
        return None
    eff_bb = float(chips) / float(bb)
    if eff_bb < 20:
        return 0
    if eff_bb < 40:
        return 1
    if eff_bb < 100:
        return 2
    return 3


def _init_player_stats(
    player_name: Optional[str],
    players_at_table: int,
    max_seats: Optional[int],
    position: Optional[str],
    stack_bucket: Optional[int],
):
    return PlayerStats(
        player_name=player_name,
        players_at_table=players_at_table,
        max_seats=max_seats,
        position=position,
        stack_bucket=stack_bucket,

        hands=1,

        # PREFLOP
        rfi=0, rfi_opp=0,
        cold_call=0, cold_call_opp=0,
        three_bet=0, three_bet_opp=0,
        fold_to_3bet=0, fold_to_3bet_opp=0,
        call_vs_3bet=0, call_vs_3bet_opp=0,
        four_bet_opp=0, four_bet=0,
        squeeze=0, squeeze_opp=0,
        steal=0, steal_opp=0,
        foldbb_vs_steal=0, foldbb_vs_steal_opp=0,

        # FLOP
        saw_flop=0,
        c_bet=0, c_bet_opp=0,
        fold_to_cbet=0, fold_to_cbet_opp=0,
        check_raise_flop=0, check_raise_flop_opp=0,
        donk_flop=0, donk_flop_opp=0,

        # TURN
        saw_turn=0,
        barrel_turn=0, barrel_turn_opp=0,
        fold_to_barrel_turn=0, fold_to_barrel_turn_opp=0,

        # RIVER
        saw_river=0,
        barrel_river=0, barrel_river_opp=0,
        fold_to_barrel_river=0, fold_to_barrel_river_opp=0,
        river_bet=0, river_bet_opp=0,

        # SHOWDOWN
        won_hand=0,
        won_without_showdown=0,
        went_showdown=0,
        won_showdown=0,
    )


def parse_stats(hand: "HandData") -> Dict[str, "PlayerStats"]:

    players: List[str] = [
        s.player_name for s in hand.seats if s.player_name and not s.sitting_out
    ]
    players_at_table = len(players)

    player_pos: Dict[str, Optional[str]] = {}
    chips_map: Dict[str, Optional[float]] = {}

    for s in hand.seats:
        if not s.player_name or s.sitting_out:
            continue
        player_pos[s.player_name] = s.position if s.position is not None else None
        chips_map[s.player_name] = s.chips

    # Big blind info
    bb: Optional[float] = None
    bb_player: Optional[str] = None
    for post in (hand.posts or []):
        if getattr(post, "kind", None) == "big blind":
            bb = getattr(post, "amount", None)
            bb_player = getattr(post, "player_name", None)
            break

    stats: Dict[str, PlayerStats] = {}
    for p in players:
        stats[p] = _init_player_stats(
            player_name=p,
            players_at_table=players_at_table,
            max_seats=hand.max_seats,
            position=player_pos.get(p),
            stack_bucket=_stack_bucket(chips_map.get(p), bb),
        )

    # --- recorrido de acciones ---
    active: Set[str] = set(players)

    # PREFLOP state
    open_raiser: Optional[str] = None
    three_bettor: Optional[str] = None
    four_bettor: Optional[str] = None
    preflop_aggressor: Optional[str] = None
    had_caller_before_3bet = False

    # Para no duplicar opp de respuesta del opener vs 3bet
    opener_response_opp_counted = False

    # BB vs steal opp
    bb_vs_steal_opp_counted = False

    # POSTFLOP state
    saw_flop: Set[str] = set()
    saw_turn: Set[str] = set()
    saw_river: Set[str] = set()

    # Flop
    flop_checked: Set[str] = set()
    flop_first_bet_by: Optional[str] = None
    did_cbet = False
    cbet_faced: Set[str] = set()

    # Turn
    turn_first_bet_by: Optional[str] = None
    did_barrel_turn = False
    barrel_turn_faced: Set[str] = set()

    # River
    river_first_bet_by: Optional[str] = None
    did_barrel_river = False
    barrel_river_faced: Set[str] = set()
    river_opp_counted: Set[str] = set()

    for ac in (hand.actions or []):
        player = getattr(ac, "player_name", None)
        if not player or player not in stats:
            continue

        street = getattr(ac, "street", None)
        action = getattr(ac, "action", None)

        # si ya foldeó, ignora (por robustez)
        if player not in active and action != "folds":
            continue

        # ---------------- PREFLOP ----------------
        if street == "preflop":

            # === OPORTUNIDADES (se cuentan cuando el jugador está en el spot) ===

            # RFI / Steal opp (solo si aún no hay open raise)
            if open_raiser is None:
                stats[player].rfi_opp += 1
                if _is_steal_pos(player_pos.get(player)):
                    stats[player].steal_opp += 1

            # Facing open y aún no hay 3bet: 3bet opp (+ squeeze opp si ya hubo caller)
            if open_raiser is not None and three_bettor is None and player != open_raiser:
                stats[player].three_bet_opp += 1
                if had_caller_before_3bet:
                    stats[player].squeeze_opp += 1

            # Facing 3bet y aún no hay 4bet: 4bet opp
            if three_bettor is not None and four_bettor is None:
                stats[player].four_bet_opp += 1

            # Opener response vs 3bet: opp de fold_to_3bet y call_vs_3bet (una vez)
            if (
                three_bettor is not None
                and open_raiser is not None
                and player == open_raiser
                and not opener_response_opp_counted
            ):
                stats[player].fold_to_3bet_opp += 1
                stats[player].call_vs_3bet_opp += 1
                opener_response_opp_counted = True

            # BB vs steal opp: cuando hay open desde CO/BTN y BB actúa (sin 3bet aún)
            if (
                bb_player is not None
                and player == bb_player
                and not bb_vs_steal_opp_counted
                and open_raiser is not None
                and three_bettor is None
                and _is_steal_pos(player_pos.get(open_raiser))
            ):
                stats[bb_player].foldbb_vs_steal_opp += 1
                bb_vs_steal_opp_counted = True

            # === ACCIÓN ===
            if action == "folds":
                # fold_to_3bet (si el que foldea es el opener vs 3bet)
                if three_bettor is not None and player == open_raiser:
                    stats[player].fold_to_3bet += 1

                # foldbb_vs_steal
                if (
                    bb_player is not None
                    and player == bb_player
                    and open_raiser is not None
                    and three_bettor is None
                    and _is_steal_pos(player_pos.get(open_raiser))
                ):
                    stats[player].foldbb_vs_steal += 1

                active.discard(player)
                continue

            if action == "raises":
                # Open raise (RFI)
                if open_raiser is None:
                    open_raiser = player
                    preflop_aggressor = player

                    stats[player].rfi += 1
                    if _is_steal_pos(player_pos.get(player)):
                        stats[player].steal += 1

                # 3bet
                elif three_bettor is None and player != open_raiser:
                    three_bettor = player
                    stats[player].three_bet += 1

                    if had_caller_before_3bet:
                        stats[player].squeeze += 1

                # 4bet
                elif three_bettor is not None and four_bettor is None:
                    four_bettor = player
                    stats[player].four_bet += 1

                continue

            if action == "calls":
                # caller antes del 3bet => squeeze spot
                if open_raiser is not None and three_bettor is None and player != open_raiser:
                    had_caller_before_3bet = True

                    # cold-call: call después de open, excluyendo BB defendiendo
                    stats[player].cold_call_opp += 1
                    if bb_player is None or player != bb_player:
                        stats[player].cold_call += 1

                # call_vs_3bet: solo si caller es el opener y no hubo 4bet
                if three_bettor is not None and player == open_raiser and four_bettor is None:
                    stats[player].call_vs_3bet += 1

                continue

            continue

        # ---------------- FLOP ----------------
        if street == "flop":
            if player in active:
                saw_flop.add(player)

            if action == "folds":
                if did_cbet and player in cbet_faced:
                    stats[player].fold_to_cbet_opp += 1
                    stats[player].fold_to_cbet += 1
                active.discard(player)
                continue

            if action == "checks":
                flop_checked.add(player)
                continue

            if action in ("bets", "raises"):
                if flop_first_bet_by is None:
                    flop_first_bet_by = player

                    # cbet opp para agresor preflop si llega al flop
                    if preflop_aggressor and preflop_aggressor in saw_flop:
                        stats[preflop_aggressor].c_bet_opp += 1

                    # cbet si el agresor hace la primera bet (bets)
                    if preflop_aggressor and player == preflop_aggressor and action == "bets":
                        did_cbet = True
                        stats[player].c_bet += 1
                        cbet_faced = {x for x in active if x != player}
                    else:
                        # donk flop: primera bet por no-agresor
                        stats[player].donk_flop_opp += 1
                        stats[player].donk_flop += 1
                else:
                    # check-raise: si había check previo y ahora raise
                    stats[player].check_raise_flop_opp += 1
                    if action == "raises" and player in flop_checked:
                        stats[player].check_raise_flop += 1

            continue

        # ---------------- TURN ----------------
        if street == "turn":
            if player in active:
                saw_turn.add(player)

            if action == "folds":
                if did_barrel_turn and player in barrel_turn_faced:
                    stats[player].fold_to_barrel_turn_opp += 1
                    stats[player].fold_to_barrel_turn += 1
                active.discard(player)
                continue

            if action in ("bets", "raises"):
                if turn_first_bet_by is None:
                    turn_first_bet_by = player

                    # barrel turn opp si hubo cbet y agresor llega al turn
                    if preflop_aggressor and did_cbet and preflop_aggressor in saw_turn:
                        stats[preflop_aggressor].barrel_turn_opp += 1

                    # barrel turn si agresor (que hizo cbet) hace primera bet del turn
                    if preflop_aggressor and did_cbet and player == preflop_aggressor and action == "bets":
                        did_barrel_turn = True
                        stats[player].barrel_turn += 1
                        barrel_turn_faced = {x for x in active if x != player}

            continue

        # ---------------- RIVER ----------------
        if street == "river":
            if player in active:
                saw_river.add(player)

            # river_bet_opp: si llega al river, 1 opp
            if player in saw_river and player not in river_opp_counted:
                stats[player].river_bet_opp += 1
                river_opp_counted.add(player)

            if action == "folds":
                if did_barrel_river and player in barrel_river_faced:
                    stats[player].fold_to_barrel_river_opp += 1
                    stats[player].fold_to_barrel_river += 1
                active.discard(player)
                continue

            if action in ("bets", "raises"):
                stats[player].river_bet += 1

                if river_first_bet_by is None:
                    river_first_bet_by = player

                    # barrel river opp si hubo barrel turn y agresor llega al river
                    if preflop_aggressor and did_barrel_turn and preflop_aggressor in saw_river:
                        stats[preflop_aggressor].barrel_river_opp += 1

                    # barrel river si agresor (que barreleó turn) hace primera bet del river
                    if preflop_aggressor and did_barrel_turn and player == preflop_aggressor and action == "bets":
                        did_barrel_river = True
                        stats[player].barrel_river += 1
                        barrel_river_faced = {x for x in active if x != player}

            continue

    # Asigna saw_* finales
    for p in players:
        stats[p].saw_flop = 1 if p in saw_flop else 0
        stats[p].saw_turn = 1 if p in saw_turn else 0
        stats[p].saw_river = 1 if p in saw_river else 0

    # --- RESULTS: winners/showdown ---
    # Mantengo tu lógica base (aunque "went_showdown" idealmente depende de si hubo showdown real)
    for p in active:
        stats[p].went_showdown = 1

    sd_number = len(active)
    if hand.results:
        for result in hand.results:
            p = result.player_name
            if not p or p not in stats:
                continue
            collected = result.collected or 0.0

            if collected > 0:
                stats[p].won_hand = 1
                if stats[p].went_showdown and sd_number > 1:
                    stats[p].won_showdown = 1
                else:
                    stats[p].won_without_showdown = 1

    return stats
