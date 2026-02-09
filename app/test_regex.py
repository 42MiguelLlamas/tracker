from __future__ import annotations
import os
import sys
import time

from pathlib import Path
from dotenv import load_dotenv

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QTimer, Qt
from PySide6.QtQuickControls2 import QQuickStyle

from .settings import MockSettings
from .database.db import DB
from .parser.main import parse_files

load_dotenv()
HH_FOLDER = os.getenv('HH_FOLDER')
TEST_FOLDER = os.getenv('TEST_FOLDER')
DB_PATH = os.getenv('DB_PATH')



def main():
    start = time.time()

    if not HH_FOLDER or not DB_PATH:
        print("Faltan variables de entorno: HH_FOLDER y/o DB_PATH")
        return 1
    
    #Init
    database = DB(DB_PATH)
    hh_folder = Path(HH_FOLDER)
    
    #Parseo
    parse_files(hh_folder, database)

    QQuickStyle.setStyle("Fusion")  # o "Material" si te gusta
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    settings = MockSettings(database)
    engine.rootContext().setContextProperty("appSettings", settings)

    engine.load(str("app/qml/App.qml"))
    if not engine.rootObjects():
        return 1
    root = engine.rootObjects()[0]
    root.setFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)

    timer = QTimer()
    timer.setInterval(1000)
    timer.timeout.connect() #Aqui supongo que me falta una funcion que runear cada x tiempo para refrescar stats no?
    timer.start()
    rc = app.exec()
    #Test de DB
    database.run_sql_file("app/tests.sql")
    database.close()

    #Cronometro
    final = time.time()
    timeConsumed = final-start
    print(timeConsumed)
    return rc

if __name__ == "__main__":
    main()
