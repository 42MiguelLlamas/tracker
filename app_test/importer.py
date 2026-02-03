from __future__ import annotations
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, Dict, List

from .db import DB

HAND_START_PREFIXES = [
    b"PokerStars Hand #",
    b"PokerStars Game #"
]

def find_hand_starts(data:bytes) -> List[int]:
    starts: List[int] = []
    for pref in HAND_START_PREFIXES:
        if data.startswith(pref):
            starts.append(0)
        needle = b"\n" + pref
        pos = 0
        while True:
            i = data.find(needle, pos)
            if i == -1:
                break
            starts.append(i + 1)
            pos = i + 1
    starts = sorted(set(starts))
    return starts

def split_complete_hands(buffer_bytes: bytes) -> Tuple[List[bytes], bytes]:
    starts = find_hand_starts(buffer_bytes)
    if len(starts) < 2:
        return [], buffer_bytes #no hay manos
    hands : List[bytes] = []
    ranges = zip(starts, starts[1:])
    for a, b in ranges:
        chunk = buffer_bytes[a:b]
        if chunk.strip():
            hands.append(chunk)
    lastStart = starts[-1]
    carry = buffer_bytes[lastStart:] #ultima mano buffer[last:]
    return hands, carry

def extract_hand_no(raw_hand:bytes) -> Optional[str]:
    for pref in HAND_START_PREFIXES:
        if raw_hand.startswith(pref):
            hash_i = raw_hand.find(b"#")
            if hash_i == -1:
                return None
            j = hash_i + 1
            digits = []
            while j < len(raw_hand):
                c = raw_hand[j]
                if 48 <= c <= 57:
                    digits.append(c)
                    j+=1
                else:
                    break
            if digits:
                return bytes(digits).decode("ascii", errors="ignore")
            return None
    return None

@dataclass
class FileRuntimeState:
    carry: bytes = b""
    last_change_ts : float = 0.0 

class HandHistoryImporter:
    def __init__(
            self,
            db: DB,
            folder: str | Path,
            window_seconds: int = 300,
            idle_flush_seconds: int = 3,
    ):
        self._bootstrapped = False
        self.db = db
        self.folder = Path(folder)
        self.window_seconds = window_seconds
        self.idle_flush_seconds = idle_flush_seconds
        self.runtime: Dict[str, FileRuntimeState] = {}
    
    def _list_txt_files(self) -> List[Path]:
        if not self.folder.exists:
            return []
        list = []
        for p in self.folder.glob("*.txt"):
            if p.is_file():
                list.append(p)
        return sorted(list)
    
    def run_initial_import(self) -> None:
        files = self._list_txt_files()

        for p in files:
            st = p.stat()
            path_str = str(p)
            mtime = float(st.st_mtime)
            size = int(st.st_size)

            self.db.upsert_file(path_str, mtime, size)
            file_id, last_offset, _, _ = self.db.get_file_state(path_str)

            rt = self.runtime.setdefault(path_str, FileRuntimeState())
            rt.last_change_ts = time.time()
            if size > last_offset:
                self._process_growth(path_str, file_id, last_offset)
            else:
                if rt.carry:
                    self._flush_carry(path_str, file_id)


    def tick(self) -> None:
        if not self._bootstrapped:
            self.run_initial_import()
            self._bootstrapped = True
            return
        now = time.time()
        cutoff = now - self.window_seconds
        files = self._list_txt_files()
        candidates: List[Tuple[Path, float, int]] = []
        #Filtrar por mtimer reciende segun cut off en funcion de window_seconds
        for p in files:
            st = p.stat()
            if st.st_mtime >= cutoff:
                candidates.append((p, float(st.st_mtime), int(st.st_size)))
        candidates.sort(key=lambda x: x[1], reverse = True)
        for p, mtime, size in candidates:
            path_str = str(p)
            file_id = self.db.upsert_file(path_str, mtime, size)
            file_id, last_offset, _, _ = self.db.get_file_state(path_str)
            rt = self.runtime.setdefault(path_str, FileRuntimeState())
            if rt.last_change_ts == 0.0:
                rt.last_change_ts = now
            changed = size > last_offset
            if changed:
                rt.last_change_ts = now
                self._process_growth(path_str, file_id, last_offset)
            else:
                if rt.carry and (now - rt.last_change_ts) >= self.idle_flush_seconds:
                    self._flush_carry(path_str, file_id)
    
    def _process_growth(self, path_str: str, file_id: int, last_offset: int) -> None:
        p = Path(path_str)
        with p.open("rb") as f:
            f.seek(last_offset, os.SEEK_SET)
            new_bytes = f.read()
            new_offset = f.tell()
        rt = self.runtime[path_str]
        buf = rt.carry + new_bytes
        hands, carry = split_complete_hands(buf)
        inserted = 0
        for raw in hands:
            hand_no = extract_hand_no(raw)
            ok = self.db.insert_hand_raw(file_id, hand_no, raw)
            if ok:
                inserted += 1
        rt.carry = carry
        self.db.update_file_offset(file_id, new_offset)
        if inserted:
            print(f"IMPORTED {Path(path_str).name}: {inserted} hands (total = {self.db.count_hands})")

    def __flush_carry(self, path_str: str, file_id: int) -> None:
        rt = self.runtime[path_str]
        raw = rt.carry
        if not raw.strip():
            rt.carry = b""
            return
        for pref in HAND_START_PREFIXES:
            if raw.startswith(pref):
                hand_no = extract_hand_no(raw)
                ok = self.db.insert_hand_raw(file_id, hand_no, raw)
                if ok:
                     print(f"[FLUSH] {Path(path_str).name}: flushed 1 hand (total={self.db.count_hands()})")
        rt.carry = b""
        




