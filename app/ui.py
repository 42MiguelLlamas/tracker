from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Qt

from .config import AppConfig, save_config
from .db import DB
from pathlib import Path
from .parser import split_hands, parse_hand_id

class MainWindow(QWidget):
    def __init__(self, cfg: AppConfig, db: DB):
        super().__init__()
        self.cfg = cfg
        self.db = db
        self.setWindowTitle("PokerTracker MVP")
        self.resize(560, 220)

        layout = QVBoxLayout()

        self.lbl_hh = QLabel()
        self.lbl_hh.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.lbl_db = QLabel()
        self.lbl_db.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.btn_pick = QPushButton("Elegir carpeta de Hand Histories…")
        self.btn_pick.clicked.connect(self.pick_folder)

        self.btn_import = QPushButton("Importar archivo HH .txt…")
        self.btn_import.clicked.connect(self.import_file)

        
        layout.addWidget(self.lbl_hh)
        layout.addWidget(self.lbl_db)
        layout.addWidget(self.btn_pick)
        layout.addWidget(self.btn_import)

        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.lbl_hh.setText(f"Carpeta HH: {self.cfg.hh_dir}")
        self.lbl_db.setText(f"Manos en DB: {self.db.hands_count()} | DB: {self.cfg.db_path}")

    def pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Selecciona la carpeta de HH", self.cfg.hh_dir)
        if path:
            self.cfg.hh_dir = path
            save_config(self.cfg)
            self.refresh()

    def import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecciona un archivo de HandHistory",
            self.cfg.hh_dir,
            "Text files (*.txt)"
        )
        if not file_path:
            return
        p = Path(file_path)
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.lbl_db.setText(f"Error leyendo archivo: {e}")
        inserted = 0
        seen = 0
        for block in split_hands(text):
            hid = parse_hand_id(block)
            if not hid:
                continue
            seen += 1
            if self.db.insert_hand(hid, block):
                inserted += 1
        self.refresh()
        self.lbl_db.setText(f"Manos en DB: {self.db.hands_count()} | +{inserted} nuevas (vistas {seen}) | DB: {self.cfg.db_path}")
