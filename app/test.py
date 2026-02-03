from pathlib import Path
from pprint import pprint

from .parser import split_hands, parse_hand


def main():
    folder = Path(r"C:\Users\llama\AppData\Local\PokerStars.ES\HandHistory\sunbreathking")
    hh_file = next(folder.glob("*.txt"))

    print("FILE:", hh_file)
    text = hh_file.read_text(encoding="utf-8", errors="replace")

    blocks = list(split_hands(text))
    print("HANDS FOUND:", len(blocks))

    # Cambia este índice para ver otra mano (0 = primera)
    i = 0
    if i >= len(blocks):
        raise SystemExit(f"Index {i} out of range (0..{len(blocks)-1})")

    block = blocks[i]
    hand = parse_hand(block)

    if not hand:
        print("parse_hand returned None")
        return

    print("\n=== HEADER ===")
    pprint(hand.get("header"), width=120)

    print("\n=== PLAYERS ===")
    for p in hand.get("players", []):
        print(
            f"Seat {p.get('seat'):>2} | {p.get('name'):<20} | stack={p.get('stack'):>7} "
            f"| pos={p.get('pos') or '-':<5} | sitting_out={p.get('sitting_out')}"
        )

    print("\n=== BLINDS / ANTE ===")
    pprint(hand.get("blinds"), width=120)

    print("\n=== HERO ===")
    pprint(hand.get("hero"), width=120)

    print("\n=== BOARD ===")
    pprint(hand.get("board"), width=120)

    print("\n=== ACTIONS ===")
    actions = hand.get("actions", {})
    for street in ["PREFLOP", "FLOP", "TURN", "RIVER"]:
        print(f"\n-- {street} --")
        for a in actions.get(street, []):
            # post actions have "what"; normal actions do not
            what = a.get("what")
            if what:
                print(f'{a["action_no"]:>2}. {a["player"]}: posts {what} {a["amount"]}')
            else:
                amt = a.get("amount")
                to_amt = a.get("to_amount")
                allin = " ALL-IN" if a.get("is_allin") else ""
                if a["type"] == "raises":
                    print(f'{a["action_no"]:>2}. {a["player"]}: raises {amt} to {to_amt}{allin}')
                elif a["type"] in ("bets", "calls"):
                    print(f'{a["action_no"]:>2}. {a["player"]}: {a["type"]} {amt}{allin}')
                else:
                    print(f'{a["action_no"]:>2}. {a["player"]}: {a["type"]}{allin}')

    print("\n=== RESULTS ===")
    pprint(hand.get("results"), width=120)

    # Si quieres ver el texto crudo de la mano, descomenta:
    # print("\n=== RAW TEXT ===")
    # print(hand.get("raw_text", ""))


if __name__ == "__main__":
    main()

