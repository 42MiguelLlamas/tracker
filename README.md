# 🂡 Poker Hand Tracker

Aplicación de escritorio en **Python + PySide6 (QML)** para importar manos de poker y mostrar estadísticas tipo **tracker (HM/PT)**.

---

## 🚀 Funcionalidades

- 📂 Importación automática de hand histories (HH)  
- ♻️ Parser incremental (solo manos nuevas)  
- 🗄️ Base de datos SQLite  
- 📊 Estadísticas:
  - RFI / Steal  
  - 3bet / 4bet / Squeeze  
  - Fold to 3bet  
  - Cold call  
  - BB vs Steal  
  - C-bet / Barrels  
- 🔄 Actualización automática cuando llegan manos nuevas  
- 🖥️ Interfaz moderna en QML  

---

## 🏗 Arquitectura

| Componente | Función |
|-----------|--------|
| **Parser** | Lee HH y guarda manos nuevas en la BD |
| **DB (SQLite)** | Fuente de verdad de manos y stats |
| **AppController** | Detecta cambios y lanza el parser |
| **Settings/Model** | Hace queries y expone stats a QML |
| **QML UI** | Muestra datos (sin lógica de BD) |

---

## ⚙️ Variables de entorno

HH_FOLDER=path/a/hand_histories
DB_PATH=path/a/database.db

---

▶️ Ejecutar
```bash
pip install -r requirements.txt
python -m app.main
```

Proyecto en desarrollo enfocado en rendimiento, arquitectura limpia y stats tipo tracker profesional.