import sys
from PySide6.QtWidgets import QApplication, QWidget

from .ui import MainWindow
from .config import load_config
from .db import DB

def main():
    app = QApplication(sys.argv)

    cfg = load_config()
    db = DB(cfg.db_path)
    print(db.list_tables())
    win = MainWindow(cfg, db)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()