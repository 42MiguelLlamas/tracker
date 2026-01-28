from pathlib import Path
from pprint import pprint
from .parser import split_hands, parse_hand

def main():

    folder = Path(r"C:\Users\llama\AppData\Local\PokerStars.ES\HandHistory\sunbreathking")
    hh_file = next(folder.glob("*.txt"))
    print(hh_file)
    text = hh_file.read_text(encoding="utf-8", errors="replace")
    
    blocks = list(split_hands(text))
    b0 = blocks[0]
    hand0 = parse_hand(b0)
    pprint(hand0, width=120)

if __name__ == "__main__":
    main()
