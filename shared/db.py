import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def service_db_path(service_name: str) -> Path:
    root = Path(os.environ.get("MONITORING_DATA", Path(__file__).resolve().parents[1] / "data"))
    root.mkdir(parents=True, exist_ok=True)
    service_dir = root / service_name
    service_dir.mkdir(parents=True, exist_ok=True)
    return service_dir / f"{service_name}.db"


def connect(service_name: str) -> sqlite3.Connection:
    connection = sqlite3.connect(service_db_path(service_name))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def session(service_name: str):
    connection = connect(service_name)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
