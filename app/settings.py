from PySide6.QtCore import QObject, Property, Signal, Slot


class MockSettings(QObject):

    handsCountChanged = Signal()

    def __init__(self, db):
        super().__init__()
        self._username = ""
        self._db = db
        self._hands_count = 0

    def getHandsCount(self) -> int:
        return self._hands_count
    @Slot()
    def refresh(self) -> None:
        new_val = self._db.count_hands()
        if new_val != self._hands_count:
            self._hands_count = new_val
            self.handsCountChanged.emit()

    @Slot(str)
    def log(self, msg: str):
        print("[QML]", msg)

    handsCount = Property(int, getHandsCount, notify=handsCountChanged)