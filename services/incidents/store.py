from shared.db import session
from shared.errors import NotFoundError

from .models import Decision, Incident

SERVICE = "incidents"

SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    detected_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(id),
    user_id INTEGER NOT NULL,
    outcome TEXT NOT NULL,
    comment TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

SEED = """
INSERT INTO incidents (id, assessment_id, status, detected_at) VALUES
    (1, 3, 'подтверждённое мошенничество', '2026-03-12T10:02:01');
INSERT INTO decisions (id, incident_id, user_id, outcome, comment, created_at) VALUES
    (1, 1, 2, 'подтверждённое мошенничество', 'Снятие в нетипичной стране выше обычного профиля', '2026-03-12T10:15:00');
"""


def ensure() -> None:
    with session(SERVICE) as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        if count == 0:
            connection.executescript(SEED)


def _one(sql: str, params: tuple, message: str):
    ensure()
    with session(SERVICE) as connection:
        row = connection.execute(sql, params).fetchone()
    if row is None:
        raise NotFoundError(message)
    return row


def _all(sql: str, params: tuple = ()):
    ensure()
    with session(SERVICE) as connection:
        return connection.execute(sql, params).fetchall()


def list_incidents() -> list[Incident]:
    return [Incident(**dict(row)) for row in _all("SELECT * FROM incidents ORDER BY id")]


def get_incident(incident_id: int) -> Incident:
    row = _one(
        "SELECT * FROM incidents WHERE id = ?",
        (incident_id,),
        f"Инцидент {incident_id} не найден",
    )
    return Incident(**dict(row))


def list_decisions(incident_id: int) -> list[Decision]:
    rows = _all(
        "SELECT * FROM decisions WHERE incident_id = ? ORDER BY id",
        (incident_id,),
    )
    return [Decision(**dict(row)) for row in rows]


def get_decision(decision_id: int) -> Decision:
    row = _one(
        "SELECT * FROM decisions WHERE id = ?",
        (decision_id,),
        f"Решение {decision_id} не найдено",
    )
    return Decision(**dict(row))
