from typing import List
from .classes import HandData


def parse_position(hand: HandData) -> HandData:
    if hand.button_pos is None or not hand.seats:
        return hand
    
    n = len(hand.seats)

    btn_seat_no = int(hand.button_pos)
    try:
        btn_idx = next(i for i, s in enumerate(hand.seats) if int(s.pos) == btn_seat_no)
    except StopIteration:
        return hand
    order = [(btn_idx + k) % n for k in range(n)]

    # etiquetas

    # positions:
    # btn = 1
    # sb = 2
    # bb = 3
    # utg = 4
    # utg+1 = 5
    # mp1 = 6
    # mp2 = 7
    # hj = 8
    # co = 9

    labels: List[str] = [""] * n
    labels[order[0]] = "BTN"
    if n == 2:
        labels[order[0]] = "SB"
        labels[order[1]] = "BB"
    if n >= 3:
        labels[order[1]] = "SB"
        labels[order[2]] = "BB"
    if n > 3:
        rest = order[3:]
        if n == 4:
            rest_names = ["UTG"]
        elif n == 5:
            rest_names = ["UTG", "CO"]
        elif n == 6:
            rest_names = ["UTG", "HJ", "CO"]
        elif n == 7:
            rest_names = ["UTG", "UTG+1", "HJ", "CO"]
        elif n == 8:
            rest_names = ["UTG", "UTG+1", "MP1", "HJ", "CO"]
        elif n == 9:
            rest_names = ["UTG", "UTG+1", "MP1", "MP2", "HJ", "CO"]
        for idx, name in zip(rest, rest_names):
            labels[idx] = name

    for s, lab in zip(hand.seats, labels):
        setattr(s, "position", lab)
    return hand