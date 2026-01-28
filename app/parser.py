import re
from typing import Dict, List, Optional, Any, Iterator

HAND_START_RE = re.compile(r"^(?:\ufeff)?PokerStars Hand #(?P<hand_id>\d+):", re.MULTILINE)
BUTTON_RE = re.compile(r"Seat #(?P<button>\d+) is the button")
SEAT_RE = re.compile(r"^Seat (?P<seat>\d+): (?P<name>.+?) \((?P<stack>\d+) in chips\)", re.MULTILINE)

# "posts small blind 10", "posts big blind 20"
POST_SB_RE = re.compile(r"^(?P<name>.+?): posts small blind (?P<amt>\d+)", re.MULTILINE)
POST_BB_RE = re.compile(r"^(?P<name>.+?): posts big blind (?P<amt>\d+)", re.MULTILINE)

# Secciones de la mano
STREET_HEADERS = ["PREFLOP", "FLOP", "TURN", "RIVER"]
SECTION_RE = re.compile(
    r"^\*\*\* (?P<section>HOLE CARDS|FLOP|TURN|RIVER|SUMMARY) \*\*\*(?: .*)?$",
    re.MULTILINE
)

# Acciones típicas (MTT)
ACTION_RE = re.compile(
    r"^(?P<name>.+?): "
    r"(?P<action>folds|checks|calls|bets|raises)"
    r"(?: (?P<a>\d+))?"
    r"(?: to (?P<to>\d+))?"
    r"(?: and is all-in)?",
    re.MULTILINE
)

POST_RE = re.compile(r"^(?P<name>.+?): posts (?P<what>the ante|small blind|big blind) (?P<amt>\d+)", re.MULTILINE)
UNCALLED_RE = re.compile(r"^Uncalled bet \((?P<amt>\d+)\) returned to (?P<name>.+)$", re.MULTILINE)
COLLECTED_RE = re.compile(r"^(?P<name>.+) collected (?P<amt>\d+) from pot", re.MULTILINE)
DONT_SHOW_RE = re.compile(r"^(?P<name>.+?): doesn't show hand", re.MULTILINE)
SHOWS_RE = re.compile(r"^(?P<name>.+?): shows \[(?P<cards>.+)\]", re.MULTILINE)
MUCKS_RE = re.compile(r"^(?P<name>.+?): mucks hand", re.MULTILINE)
DEALT_RE = re.compile(r"^Dealt to (?P<name>\S+) \[(?P<c1>..)\s+(?P<c2>..)\]", re.MULTILINE)

def split_hands(text: str) -> Iterator[str]:
    matches = list(HAND_START_RE.finditer(text))
    if not matches:
        return
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield text[start:end].strip()

def _extract_section_text(block: str) -> Dict[str, str]:
    """
    Devuelve texto por sección: HOLE CARDS (lo tratamos como PREFLOP), FLOP, TURN, RIVER, SUMMARY.
    """
    sections: Dict[str, str] = {}
    matches = list(SECTION_RE.finditer(block))
    if not matches:
        return sections

    for i, m in enumerate(matches):
        sec = m.group("section")
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        sections[sec] = block[start:end]
    return sections
def _pos_from_button_and_blinds(
    seats_in_hand: List[int],
    button_seat: Optional[int],
    sb_seat: Optional[int],
    bb_seat: Optional[int],
) -> Dict[int, str]:
    """
    Asigna posiciones preflop aproximadas basadas en BTN/SB/BB y el orden de asientos.
    Recorre en sentido horario por número de asiento (ordenado) y hace wrap-around.

    Requisitos para que sea fiable:
      - Tener bb_seat (idealmente también sb_seat y button_seat).
    """
    pos: Dict[int, str] = {}
    if not seats_in_hand:
        return pos

    ordered = sorted(seats_in_hand)

    def next_seat(cur: int) -> int:
        idx = ordered.index(cur)
        return ordered[(idx + 1) % len(ordered)]

    # Marca posiciones fijas si existen
    if button_seat in ordered:
        pos[button_seat] = "BTN"
    if sb_seat in ordered:
        pos[sb_seat] = "SB"
    if bb_seat in ordered:
        pos[bb_seat] = "BB"

    # Si no tenemos BB no podemos asignar el resto de forma consistente
    if bb_seat not in ordered or len(ordered) < 3:
        return pos

    n = len(ordered)

    # Etiquetas para posiciones "no ciegas"
    # Estas se asignan empezando por el asiento a la izquierda de BB (UTG) y avanzando.
    if n == 3:
        labels = ["UTG"]
    elif n == 4:
        labels = ["UTG", "CO"]
    elif n == 5:
        labels = ["UTG", "HJ", "CO"]
    elif n == 6:
        labels = ["UTG", "HJ", "CO"]
    else:
        # 7/8/9-max (si hay 7 u 8, se usarán las primeras)
        labels = ["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"]

    cur = next_seat(bb_seat)
    li = 0
    while cur != bb_seat:
        # Saltamos asientos ya etiquetados (BTN/SB/BB)
        if cur not in pos:
            if li < len(labels):
                pos[cur] = labels[li]
            else:
                # Por si hay más asientos de los previstos, etiqueta genérica
                pos[cur] = f"MP{li - len(labels) + 1}"
            li += 1
        cur = next_seat(cur)

    return pos

def parse_special_lines(text: str, results: Dict) -> List:
    for m in UNCALLED_RE.finditer(text):
        results["uncalled"].append({"player": m.group("name").strip(), "amount": int(m.group("amt"))})
    for m in COLLECTED_RE.finditer(text):
        results["collected"].append({"player": m.group("name").strip(), "amount": int(m.group("amt"))})
    for m in SHOWS_RE.finditer(text):
        results["showdown"].append({"player": m.group("name").strip(), "type": "shows", "cards": m.group("cards")})
    for m in DONT_SHOW_RE.finditer(text):
        results["showdown"].append({"player": m.group("name").strip(), "type": "doesnt_show"})
    for m in MUCKS_RE.finditer(text):
        results["showdown"].append({"player": m.group("name").strip(), "type": "mucks"})

def parse_hand(block: str) -> Optional[Dict[str, Any]]:
    # hand_id
    hm = HAND_START_RE.search(block)
    if not hm:
        return None
    hand_id = hm.group("hand_id")

    # button
    bm = BUTTON_RE.search(block)
    button_seat = int(bm.group("button")) if bm else None

    # seats/players
    players: List[Dict[str, Any]] = []
    seat_to_name: Dict[int, str] = {}
    for sm in SEAT_RE.finditer(block):
        seat = int(sm.group("seat"))
        name = sm.group("name").strip()
        stack = int(sm.group("stack"))
        players.append({"seat": seat, "name": name, "stack": stack})
        seat_to_name[seat] = name

    # blinds (name + amount) y deducir seat de SB/BB a partir del name
    sb = None
    bb = None
    sb_seat = None
    bb_seat = None

    sbm = POST_SB_RE.search(block)
    if sbm:
        sb = int(sbm.group("amt"))
        sb_name = sbm.group("name").strip()
        # encuentra seat por nombre
        for p in players:
            if p["name"] == sb_name:
                sb_seat = p["seat"]
                break

    bbm = POST_BB_RE.search(block)
    if bbm:
        bb = int(bbm.group("amt"))
        bb_name = bbm.group("name").strip()
        for p in players:
            if p["name"] == bb_name:
                bb_seat = p["seat"]
                break

    # posiciones
    seats_in_hand = [p["seat"] for p in players]
    pos_by_seat = _pos_from_button_and_blinds(seats_in_hand, button_seat, sb_seat, bb_seat)
    for p in players:
        p["pos"] = pos_by_seat.get(p["seat"])

    # hero + cartas
    hero_name = None
    hero_cards = None
    dm = DEALT_RE.search(block)
    if dm:
        hero_name = dm.group("name")
        hero_cards = [dm.group("c1"), dm.group("c2")]

    # secciones y acciones
    sections = _extract_section_text(block)
    print("SECTIONS:", list(sections.keys()))
    results = {
        "uncalled": [],
        "collected": [],
        "showdown": []
    }
    parse_special_lines(block, results)
    actions_by_street: Dict[str, List[Dict[str, Any]]] = {"PREFLOP": [], "FLOP": [], "TURN": [], "RIVER": []}

    def parse_actions(text: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        action_no = 0
        for am in ACTION_RE.finditer(text):
            line = am.group(0)

            action_no += 1
            name = am.group("name").strip()
            action = am.group("action").strip()
            a = am.group("a")
            to = am.group("to")

            is_allin = "all-in" in line

            out.append({
                "action_no": action_no,
                "player": name,
                "type": action,
                "amount": int(a) if a else None,
                "to_amount": int(to) if to else None,
                "is_allin": is_allin,
            })

        return out

    # HOLE CARDS = preflop actions
    if "HOLE CARDS" in sections:
        actions_by_street["PREFLOP"] = parse_actions(sections["HOLE CARDS"])
    if "FLOP" in sections:
        actions_by_street["FLOP"] = parse_actions(sections["FLOP"])
    if "TURN" in sections:
        actions_by_street["TURN"] = parse_actions(sections["TURN"])
    if "RIVER" in sections:
        actions_by_street["RIVER"] = parse_actions(sections["RIVER"])

    return {
        "hand_id": hand_id,
        "button_seat": button_seat,
        "blinds": {"sb": sb, "bb": bb, "sb_seat": sb_seat, "bb_seat": bb_seat},
        "players": sorted(players, key=lambda x: x["seat"]),
        "hero": {"name": hero_name, "cards": hero_cards},
        "actions": actions_by_street,
        "results" : results
    }
