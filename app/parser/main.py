from typing import List, Iterator, Any
from pathlib import Path
from .parse_hand import parse_hand

def iter_hands(fp, start_offset: int) -> Iterator[List[bytes]]:
    cur: List[bytes] = []
    fp.seek(start_offset)
    started = False
    first_line = True

    for line in fp:
        line_end_offset = fp.tell()

        if first_line:
            first_line = False
            if start_offset==0 and line.startswith(b"\xef\xbb\xbf"):
                line = line[3:]

        if line.startswith(b"PokerStars Hand"):
            if started and cur:
                yield cur, prev_offset
                cur = []
            started = True
        if started:
            cur.append(line)
        prev_offset = line_end_offset
    if started and cur:
        yield cur, prev_offset

def list_txt_files(folder: Path) -> List[Path]:
        if not folder.exists():
            return []
        files: List[Path] = []
        for p in folder.glob("*.txt"):
            if p.is_file():
                files.append(p)
        return sorted(files)


def parse_files(hh_folder: Path, database: Any) -> None:
    files = list_txt_files(hh_folder)
    hands = []
    for file_path in files:
        st = file_path.stat() #metadatos del archivo
        path_str = str(file_path) 
        mtime = float(st.st_mtime) #fecha de modificacion
        current_size = int(st.st_size) #file size

        database.upsert_file(path_str, mtime, current_size)
        file_id, last_offset = database.get_file_state(path_str)

        if current_size <= last_offset:
            continue

        with file_path.open("rb") as f:
            new_offset = last_offset
            for hand_lines, end_offset in iter_hands(f, last_offset):
                new_offset = end_offset
                hand = parse_hand(hand_lines)
                hands.append(hand)
                database.insert_hand(file_id=file_id, hand=hand)

        database.set_file_offset(file_id=file_id, last_offset=new_offset, mtime=mtime, size=current_size)
