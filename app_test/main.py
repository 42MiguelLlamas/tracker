from pathlib import Path
import sys
from dotenv import load_dotenv
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, Qt
from PySide6.QtQuickControls2 import QQuickStyle
from .settings import MockSettings
from .db import DB
from .importer import HandHistoryImporter

load_dotenv()
FOLDER = os.getenv('FOLDER')
def on_tick(importer, appSettings) -> None:
    importer.tick()
    appSettings.refresh()


def main():
    QQuickStyle.setStyle("Fusion")  # o "Material" si te gusta
    base_dir = Path(__file__).parent
    qml_path = base_dir / "qml" / "App.qml"

    #DB
    db_path = base_dir / "poker.sqlite3"
    db = DB(db_path)
    folder = FOLDER
    importer = HandHistoryImporter(
        db=db,
        folder=folder,
        window_seconds=300,
        idle_flush_seconds=200,
    )

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    settings = MockSettings(db)
    engine.rootContext().setContextProperty("appSettings", settings)

    engine.load(str(qml_path))

    if not engine.rootObjects():
        return 1
    root = engine.rootObjects()[0]
    root.setFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

    timer = QTimer()
    timer.setInterval(1000)
    timer.timeout.connect(lambda: on_tick(importer, settings))
    timer.start()
    rc = app.exec()
    db.close()
    return rc


if __name__ == "__main__":
    sys.exit(main())
