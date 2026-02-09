from __future__ import annotations
from .classes import *
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional


def _safe_repr(v: Any) -> str:
    if v is None:
        return "None"
    if isinstance(v, float):
        # evita notación científica rara en logs
        return f"{v:.10g}"
    return repr(v)


def _dump(obj: Any, indent: int = 0, sort_dict_keys: bool = True) -> str:
    """
    Pretty printer recursivo para dataclasses / dict / list.
    Devuelve string (para print o logging).
    """
    pad = " " * indent

    if is_dataclass(obj):
        cls = obj.__class__.__name__
        d = asdict(obj)
        lines = [f"{pad}{cls}("]
        for k in sorted(d.keys()) if sort_dict_keys else d.keys():
            lines.append(f"{pad}  {k}={_dump(d[k], indent + 4, sort_dict_keys)},")
        lines.append(f"{pad})")
        return "\n".join(lines)

    if isinstance(obj, dict):
        if not obj:
            return f"{pad}{{}}"
        keys = sorted(obj.keys()) if sort_dict_keys else obj.keys()
        lines = [f"{pad}{{"]
        for k in keys:
            lines.append(f"{pad}  {_safe_repr(k)}: {_dump(obj[k], indent + 4, sort_dict_keys)},")
        lines.append(f"{pad}}}")
        return "\n".join(lines)

    if isinstance(obj, list):
        if not obj:
            return f"{pad}[]"
        lines = [f"{pad}["]
        for item in obj:
            lines.append(f"{_dump(item, indent + 2, sort_dict_keys)},")
        lines.append(f"{pad}]")
        return "\n".join(lines)

    # tipos simples
    return f"{pad}{_safe_repr(obj)}"


def print_hand_full(hand: "HandData", *, sort_dict_keys: bool = True) -> None:
    """
    Imprime ABSOLUTAMENTE TODO el HandData (incluye seats/posts/dealt/actions/stats/board/results)
    con formato legible y recursivo.

    Uso:
        print_hand_full(hand)
    """
    print("=" * 80)
    print(_dump(hand, indent=0, sort_dict_keys=sort_dict_keys))
    print("=" * 80)


def print_hand(hand: HandData) -> None:
    """
    Imprime TODO pero por secciones (más cómodo para debug poker).
    Incluye también stats por jugador con todas las claves.
    """
    print("=" * 80)
    print(f"HAND #{hand.hand_id}  tournament={hand.tournament_id}  dt={hand.local_dt} {hand.local_tz}")
    print("-" * 80)

    # Header bruto
    print(">>> HEADER")
    for k in [
        "hand_id", "tournament_id", "buy_in", "stakes", "cur", "local_dt", "local_tz",
        "max_seats", "players_seated", "button_pos"
    ]:
        print(f"{k:>16}: {_safe_repr(getattr(hand, k, None))}")

    # Seats
    print("\n>>> SEATS")
    for s in hand.seats:
        print(_dump(s, indent=2))

    # Posts
    print("\n>>> POSTS")
    for p in hand.posts:
        print(_dump(p, indent=2))

    # Dealt
    print("\n>>> DEALT")
    print(_dump(hand.dealt, indent=2))

    # Actions
    print("\n>>> ACTIONS")
    for a in hand.actions:
        print(_dump(a, indent=2))

    # Board
    print("\n>>> BOARD")
    print(_dump(hand.board, indent=2))

    # Results
    print("\n>>> RESULTS")
    for r in hand.results:
        print(_dump(r, indent=2))

    # Stats
    print("\n>>> STATS")
    if not hand.stats:
        print("  (empty)")
    else:
        # hand.stats: Dict[str, PlayerStats]
        for player_name, st in hand.stats.items():
            print(f"\n  -- {player_name} --")
            print(_dump(st, indent=4))

    print("=" * 80)
