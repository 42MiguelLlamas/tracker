import sqlite3
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot


def default_db_path(app_name: str = "PokerAssistant") -> Path:
    base = Path.home() / f".{app_name.lower()}"
    base.mkdir(parents=True, exist_ok=True)
    return base / "app.db"

class MockSettings(QObject):
    usernameChanged = Signal()
    handsFolderChanged = Signal()
    configuredChanged = Signal()

    def __init__(self):
        super().__init__()
        self._username = ""
        self._folder = ""

    @Slot(str)
    def log(self, msg: str):
        print("[QML]", msg)

    # --- username ---
    def getUsername(self):
        return self._username

    def setUsername(self, v):
        if v != self._username:
            self._username = v
            self.usernameChanged.emit()
            self.configuredChanged.emit()

    # --- folder ---
    def getFolder(self):
        return self._folder

    def setFolder(self, v):
        if v != self._folder:
            self._folder = v
            self.handsFolderChanged.emit()
            self.configuredChanged.emit()

    # --- configured ---
    def getConfigured(self):
        return bool(self._username and self._folder)

    username = Property(str, getUsername, setUsername, notify=usernameChanged)
    handsFolder = Property(str, getFolder, setFolder, notify=handsFolderChanged)
    configured = Property(bool, getConfigured, notify=configuredChanged)

class SettingsStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or default_db_path()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            con.commit()

    def get(self, key: str) -> str | None:
        with self._connect() as con:
            row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None

    def set(self, key: str, value: str) -> None:
        with self._connect() as con:
            con.execute("""
                INSERT INTO settings(key, value)
                VALUES(?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            con.commit()

    def delete(self, key: str) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM settings WHERE key = ?", (key,))
            con.commit()
