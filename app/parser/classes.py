from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Seat:
    pos: str | None = None
    player_name: str | None = None
    chips: float | None = None
    bounty: float | None = None
    sitting_out: bool = False
    position: str | None = None

@dataclass
class Action:
    street:str | None = None
    player_name:str | None = None
    action:str | None = None
    amount:float | None = None
    raise_from: float | None = None
    raise_to: float | None = None
    is_all_in: bool = False

@dataclass
class Post:
    player_name: str | None = None
    kind: str | None = None
    amount: float | None = None

@dataclass
class PlayerResult:
    player_name: str | None = None
    cards: str | None = None
    collected: float | None = None

@dataclass
class HandData:
    hand_id: str | None
    tournament_id: str | None
    buy_in: str | None
    stakes: str | None
    cur: str | None
    local_dt: str | None
    local_tz: str | None

    max_seats: int | None
    button_pos: int | None
    players_seated : int | None

    seats: List[Seat] = field(default_factory=list)
    posts: List[Post] = field(default_factory=list)
    dealt: Dict[str,str] = field(default_factory=dict)
    actions: List[Action] = field(default_factory=list)
    stats: Dict[str, PlayerStats] = field(default_factory=dict)

    board: Dict[str, str] = field(default_factory=dict)
    results: List[PlayerResult] = field(default_factory=list)


@dataclass
class PlayerStats:
    player_name: str | None
    players_at_table: int | None
    max_seats: int | None
    position: str | None
    stack_bucket : int |None # 0=0-20bb,1=20-40,2=40-100,3=100+

    hands:  int | None

    #PREFLOP
    rfi: int | None
    rfi_opp: int | None

    cold_call: int | None
    cold_call_opp: int | None


    three_bet:  int | None
    three_bet_opp: int | None
    fold_to_3bet: int | None
    fold_to_3bet_opp: int | None
    call_vs_3bet: int | None
    call_vs_3bet_opp: int | None

    four_bet_opp: int | None
    four_bet:  int | None

    squeeze: int | None
    squeeze_opp: int | None

    steal: int | None
    steal_opp: int | None

    foldbb_vs_steal: int | None
    foldbb_vs_steal_opp: int | None

    #FLOP
    saw_flop: int | None

    c_bet: int | None
    c_bet_opp: int | None

    fold_to_cbet: int | None
    fold_to_cbet_opp: int | None

    check_raise_flop: int | None
    check_raise_flop_opp: int | None

    donk_flop: int | None
    donk_flop_opp: int | None

    #TURN
    saw_turn : int | None

    barrel_turn: int | None
    barrel_turn_opp: int | None

    fold_to_barrel_turn: int | None
    fold_to_barrel_turn_opp: int | None

    #RIVER

    saw_river : int | None

    barrel_river: int | None
    barrel_river_opp: int | None

    fold_to_barrel_river: int | None
    fold_to_barrel_river_opp: int | None

    river_bet: int | None
    river_bet_opp: int | None

    #SHOWDOWN
    won_hand: int | None
    won_without_showdown: int | None

    went_showdown: int | None
    won_showdown: int | None