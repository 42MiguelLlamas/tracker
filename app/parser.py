import re
from typing import Dict, List, Optional, Any, Iterator, Tuple

HAND_START_RE = re.compile(r"^(?:\ufeff)?PokerStars Hand #(?P<hand_id>\d+):", re.MULTILINE)

# Header metadata
TOURNEY_RE = re.compile(r"Tournament #(?P<tournament_id>\d+)")
BUYIN_RE = re.compile(
    r",\s*(?P<sym>€|\$|£)?(?P<buyin>\d+(?:\.\d+)?)\+(?P<fee>\d+(?:\.\d+)?)\s*(?P<ccy>[A-Z]{3})"
)
LEVEL_RE = re.compile(r"\bLevel\s+(?P<level>[IVXLCDM]+)\b")
BLINDS_LEVEL_RE = re.compile(r"\((?P<sb>\d+)\/(?P<bb>\d+)\)")
DATETIME_RE = re.compile(r"-\s*(?P<date>\d{4}/\d{2}/\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<tz>[A-Z]{2,5})")
TABLE_RE = re.compile(r"^Table '(?P<table>[^']+)'", re.MULTILINE)
MAX_RE = re.compile(r"\b(?P<max>\d+)-max\b")
BUTTON_RE = re.compile(r"Seat #(?P<button>\d+) is the button")

# Seats / players
SEAT_RE = re.compile(r"^Seat (?P<seat>\d+): (?P<name>.+?) \((?P<stack>\d+) in chips\)(?P<rest>.*)$", re.MULTILINE)

# Posts (antes & blinds)
POST_RE = re.compile(
    r"^(?P<name>.+?): posts (?P<what>the ante|small blind|big blind) (?P<amt>\d+)",
    re.MULTILINE
)

SECTION_RE = re.compile(
    r"^\*\*\* (?P<section>HOLE CARDS|FLOP|TURN|RIVER|SHOW DOWN|SUMMARY) \*\*\*(?: .*)?$",
    re.MULTILINE
)

ACTION_RE = re.compile(
    r"^(?P<name>.+?): "
    r"(?P<action>folds|checks|calls|bets|raises)"
    r"(?: (?P<a>\d+))?"
    r"(?: to (?P<to>\d+))?"
    r"(?P<allin> and is all-in)?",
    re.MULTILINE
)

# Special/result lines
UNCALLED_RE = re.compile(r"^Uncalled bet \((?P<amt>\d+)\) returned to (?P<name>.+)$", re.MULTILINE)
COLLECTED_RE = re.compile(r"^(?P<name>.+) collected (?P<amt>\d+) from pot", re.MULTILINE)

DONT_SHOW_RE = re.compile(r"^(?P<name>.+?): doesn't show hand", re.MULTILINE)
SHOWS_RE = re.compile(r"^(?P<name>.+?): shows \[(?P<cards>.+)\]", re.MULTILINE)
MUCKS_RE = re.compile(r"^(?P<name>.+?): mucks hand", re.MULTILINE)

DEALT_RE = re.compile(r"^Dealt to (?P<name>\S+) \[(?P<c1>..)\s+(?P<c2>..)\]", re.MULTILINE)

# Pots & board from SUMMARY
TOTAL_POT_RE = re.compile(r"^Total pot (?P<pot>\d+)\s+\|\s+Rake (?P<rake>\d+)", re.MULTILINE)
BOARD_SUMMARY_RE = re.compile(r"^Board \[(?P<board>.+)\]", re.MULTILINE)

# Board in street headers (helps if you want it earlier too)
FLOP_HDR_RE = re.compile(r"^\*\*\* FLOP \*\*\* \[(?P<f1>..)\s+(?P<f2>..)\s+(?P<f3>..)\]", re.MULTILINE)
TURN_HDR_RE = re.compile(r"^\*\*\* TURN \*\*\* \[(?P<flop>.+?)\] \[(?P<turn>..)\]", re.MULTILINE)
RIVER_HDR_RE = re.compile(r"^\*\*\* RIVER \*\*\* \[(?P<turnboard>.+?)\] \[(?P<river>..)\]", re.MULTILINE)

FINISH_RE = re.compile(r"^(?P<name>.+) finished the tournament in (?P<place>\d+)(?:st|nd|rd|th) place$", re.MULTILINE)
TICKET_RE = re.compile(r"^(?P<name>.+) wins a '(?P<ticket>.+)' ticket$", re.MULTILINE)

# ----------------------------
# Splitting hands
# ----------------------------

def split_hands(text: str) -> Iterator[str]:
    matches = list(HAND_START_RE.finditer(text))
    if not matches:
        return
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        yield text[start:end].strip()

# ----------------------------
# Section extraction
# ----------------------------

def parse_tournament_result(block: str) -> dict:
    out = {"player": None, "finish_place": None, "prize_type": None, "prize_amount": None, "prize_desc": None}

    m = FINISH_RE.search(block)
    if m:
        out["player"] = m.group("name").strip()
        out["finish_place"] = int(m.group("place"))

    m = TICKET_RE.search(block)
    if m:
        out["player"] = out["player"] or m.group("name").strip()
        out["prize_type"] = "ticket"
        out["prize_desc"] = m.group("ticket").strip()

    return out


def _extract_section_text(block: str) -> Dict[str, str]:
    """
    Returns raw text per section:
      HOLE CARDS, FLOP, TURN, RIVER, SHOW DOWN, SUMMARY
    The captured text is the substring AFTER the section header line until the next section.
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


# ----------------------------
# Positions helper
# ----------------------------

def _pos_from_button_and_blinds(
    seats_in_hand: List[int],
    button_seat: Optional[int],
    sb_seat: Optional[int],
    bb_seat: Optional[int],
) -> Dict[int, str]:
    """
    Assign preflop positions based on BTN/SB/BB and seat order.
    """
    pos: Dict[int, str] = {}
    if not seats_in_hand:
        return pos

    ordered = sorted(seats_in_hand)

    def next_seat(cur: int) -> int:
        idx = ordered.index(cur)
        return ordered[(idx + 1) % len(ordered)]

    if button_seat in ordered:
        pos[button_seat] = "BTN"
    if sb_seat in ordered:
        pos[sb_seat] = "SB"
    if bb_seat in ordered:
        pos[bb_seat] = "BB"

    if bb_seat not in ordered or len(ordered) < 3:
        return pos

    n = len(ordered)
    if n == 3:
        labels = ["UTG"]
    elif n == 4:
        labels = ["UTG", "CO"]
    elif n == 5:
        labels = ["UTG", "HJ", "CO"]
    elif n == 6:
        labels = ["UTG", "HJ", "CO"]
    else:
        labels = ["UTG", "UTG+1", "UTG+2", "LJ", "HJ", "CO"]

    cur = next_seat(bb_seat)
    li = 0
    while cur != bb_seat:
        if cur not in pos:
            if li < len(labels):
                pos[cur] = labels[li]
            else:
                pos[cur] = f"MP{li - len(labels) + 1}"
            li += 1
        cur = next_seat(cur)

    return pos


# ----------------------------
# Parsing helpers
# ----------------------------

def _parse_header(block: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "tournament_id": None,
        "buyin": None,
        "fee": None,
        "currency": None,
        "total_buyin": None,
        "level": None,
        "sb_level": None,
        "bb_level": None,
        "played_at": None,   # "YYYY/MM/DD HH:MM:SS"
        "tz": None,
        "table_name": None,
        "max_seats": None,
        "button_seat": None,
    }

    m = TOURNEY_RE.search(block)
    if m:
        out["tournament_id"] = m.group("tournament_id")

    m = BUYIN_RE.search(block)
    if m:
        buyin = float(m.group("buyin"))
        fee = float(m.group("fee"))
        out["buyin"] = buyin
        out["fee"] = fee
        out["currency"] = m.group("ccy")
        out["total_buyin"] = buyin + fee

    m = LEVEL_RE.search(block)
    if m:
        out["level"] = m.group("level")

    m = BLINDS_LEVEL_RE.search(block)
    if m:
        out["sb_level"] = int(m.group("sb"))
        out["bb_level"] = int(m.group("bb"))

    m = DATETIME_RE.search(block)
    if m:
        out["played_at"] = f"{m.group('date')} {m.group('time')}"
        out["tz"] = m.group("tz")

    m = TABLE_RE.search(block)
    if m:
        out["table_name"] = m.group("table")

    m = MAX_RE.search(block)
    if m:
        out["max_seats"] = int(m.group("max"))

    m = BUTTON_RE.search(block)
    if m:
        out["button_seat"] = int(m.group("button"))

    return out


def _parse_posts(block: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Returns:
      posts_actions: list of actions to prepend to PREFLOP
      blinds_info: dict with sb/bb/ante + corresponding seats if known later
    """
    posts: List[Dict[str, Any]] = []
    blinds_info: Dict[str, Any] = {"ante": None, "sb": None, "bb": None, "sb_seat": None, "bb_seat": None}

    n = 0
    for m in POST_RE.finditer(block):
        n += 1
        who = m.group("name").strip()
        what = m.group("what")
        amt = int(m.group("amt"))
        posts.append({
            "action_no": n,
            "player": who,
            "type": "posts",
            "what": what,       # "the ante" / "small blind" / "big blind"
            "amount": amt,
            "to_amount": None,
            "is_allin": False,
        })

        if what == "the ante":
            # usually same for everyone; keep first seen
            if blinds_info["ante"] is None:
                blinds_info["ante"] = amt
        elif what == "small blind":
            blinds_info["sb"] = amt
        elif what == "big blind":
            blinds_info["bb"] = amt

    return posts, blinds_info


def _parse_actions(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    action_no = 0
    for am in ACTION_RE.finditer(text):
        action_no += 1
        name = am.group("name").strip()
        action = am.group("action").strip()
        a = am.group("a")
        to = am.group("to")
        is_allin = am.group("allin") is not None

        out.append({
            "action_no": action_no,
            "player": name,
            "type": action,  # folds/checks/calls/bets/raises
            "amount": int(a) if a else None,
            "to_amount": int(to) if to else None,
            "is_allin": is_allin,
        })
    return out


def parse_special_lines(text: str, results: Dict[str, Any]) -> None:
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


def _parse_pot_and_board(block: str, sections: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "total_pot": None,
        "rake": None,
        "board": {"flop": None, "turn": None, "river": None, "all": None},
    }

    # Total pot / rake typically in SUMMARY
    summary = sections.get("SUMMARY", "")
    m = TOTAL_POT_RE.search(summary)
    if m:
        out["total_pot"] = int(m.group("pot"))
        out["rake"] = int(m.group("rake"))

    # Board from SUMMARY (works even when SHOW DOWN exists)
    m = BOARD_SUMMARY_RE.search(summary)
    if m:
        cards = m.group("board").strip().split()
        out["board"]["all"] = cards
        if len(cards) >= 3:
            out["board"]["flop"] = cards[:3]
        if len(cards) >= 4:
            out["board"]["turn"] = cards[3]
        if len(cards) >= 5:
            out["board"]["river"] = cards[4]
        return out

    # Fallback: parse board from street headers (if summary missing or weird)
    m = FLOP_HDR_RE.search(block)
    if m:
        out["board"]["flop"] = [m.group("f1"), m.group("f2"), m.group("f3")]
    m = TURN_HDR_RE.search(block)
    if m:
        out["board"]["turn"] = m.group("turn")
    m = RIVER_HDR_RE.search(block)
    if m:
        out["board"]["river"] = m.group("river")

    # Build "all" if we have it
    all_cards: List[str] = []
    if out["board"]["flop"]:
        all_cards.extend(out["board"]["flop"])
    if out["board"]["turn"]:
        all_cards.append(out["board"]["turn"])
    if out["board"]["river"]:
        all_cards.append(out["board"]["river"])
    out["board"]["all"] = all_cards if all_cards else None

    return out


# ----------------------------
# Main parse function
# ----------------------------

def parse_hand(block: str) -> Optional[Dict[str, Any]]:
    hm = HAND_START_RE.search(block)
    if not hm:
        return None

    # Header metadata
    header = _parse_header(block)
    hand_id = hm.group("hand_id")
    button_seat = header.get("button_seat")

    # Sections
    sections = _extract_section_text(block)

    # Seats / players
    players: List[Dict[str, Any]] = []
    for sm in SEAT_RE.finditer(block):
        seat = int(sm.group("seat"))
        name = sm.group("name").strip()
        stack = int(sm.group("stack"))
        rest = sm.group("rest") or ""
        is_sitting_out = "is sitting out" in rest
        players.append({"seat": seat, "name": name, "stack": stack, "sitting_out": is_sitting_out})

    # Posts: ante/sb/bb as actions + blinds info
    post_actions, blinds_info = _parse_posts(block)

    # Deduce sb_seat/bb_seat from posts (names) by matching to players list
    sb_seat = None
    bb_seat = None
    for a in post_actions:
        if a["what"] == "small blind":
            for p in players:
                if p["name"] == a["player"]:
                    sb_seat = p["seat"]
                    break
        elif a["what"] == "big blind":
            for p in players:
                if p["name"] == a["player"]:
                    bb_seat = p["seat"]
                    break
    blinds_info["sb_seat"] = sb_seat
    blinds_info["bb_seat"] = bb_seat

    # Positions
    seats_in_hand = [p["seat"] for p in players]
    pos_by_seat = _pos_from_button_and_blinds(seats_in_hand, button_seat, sb_seat, bb_seat)
    for p in players:
        p["pos"] = pos_by_seat.get(p["seat"])

    # Hero + cards
    hero_name = None
    hero_cards = None
    dm = DEALT_RE.search(block)
    if dm:
        hero_name = dm.group("name")
        hero_cards = [dm.group("c1"), dm.group("c2")]

    # Actions by street
    actions_by_street: Dict[str, List[Dict[str, Any]]] = {"PREFLOP": [], "FLOP": [], "TURN": [], "RIVER": []}

    preflop = _parse_actions(sections.get("HOLE CARDS", ""))
    # Renumber preflop actions after posts
    for i, a in enumerate(preflop, start=len(post_actions) + 1):
        a["action_no"] = i
    actions_by_street["PREFLOP"] = post_actions + preflop

    actions_by_street["FLOP"] = _parse_actions(sections.get("FLOP", ""))
    actions_by_street["TURN"] = _parse_actions(sections.get("TURN", ""))
    actions_by_street["RIVER"] = _parse_actions(sections.get("RIVER", ""))

    # Results
    results: Dict[str, Any] = {
        "uncalled": [],
        "collected": [],
        "showdown": [],
        "total_pot": None,
        "rake": None,
    }
    parse_special_lines(block, results)

    pot_board = _parse_pot_and_board(block, sections)
    results["total_pot"] = pot_board["total_pot"]
    results["rake"] = pot_board["rake"]

    # Mapear cartas mostradas a jugadores (mejor como lista de 2 cartas)
    shown_map = {}
    for s in results["showdown"]:
        if s.get("type") == "shows" and s.get("cards"):
            shown_map[s["player"]] = s["cards"].split()

    for p in players:
        p["show_cards"] = shown_map.get(p["name"])  # None si no mostró

    tres = parse_tournament_result(block)

    return {
        "hand_id": hand_id,
        "header": header,
        "players": sorted(players, key=lambda x: x["seat"]),
        "hero": {"name": hero_name, "cards": hero_cards},
        "blinds": blinds_info,
        "actions": actions_by_street,
        "board": pot_board["board"],
        "results": results,
        "raw_text": block,
        "tres" : tres
    }
