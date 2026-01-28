import json
import os
from dataclasses import dataclass
from pathlib import Path

APP_NAME= "PokerTrackerMVP"

def appdata_dir() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home)))
    p = base / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p

def config_path() -> Path:
    return appdata_dir() / "config.json"

@dataclass
class AppConfig:
    hh_dir : str
    db_path : str

def load_config()-> AppConfig:
    cp = config_path()
    if cp.exists() and cp.is_dir():
        cp.rename(cp.with_name("config_json_OLD"))
    if cp.exists():
        try:
            data = json.loads(cp.read_text(encoding="utf-8"))
            return AppConfig(
                hh_dir=data.get("hh_dir", str(Path.home())),
                db_path=data.get("db_path", str(appdata_dir()/"tracker.db"))
                )
        except Exception:
            pass
    cfg = AppConfig(
        hh_dir=str(Path.home()),
        db_path=str(appdata_dir()/"tracker.db")
        )
    save_config(cfg)
    return cfg

def save_config(cfg: AppConfig) -> None:
    config_path().write_text(
        json.dumps({"hh_dir":cfg.hh_dir, "db_path" : cfg.db_path}, indent=2),
        encoding="utf-8"
    )
    