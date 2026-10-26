from shared.db import session
from shared.errors import NotFoundError

from .models import Assessment, Rule, RuleHit, Threshold

SERVICE = "risk"

SCHEMA = """
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY,
    condition TEXT NOT NULL,
    score_weight INTEGER NOT NULL,
    state TEXT NOT NULL,
    author_id INTEGER NOT NULL,
    approver_id INTEGER,
    created_at TEXT NOT NULL,
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY,
    subject_type TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    recommendation TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rule_hits (
    id INTEGER PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES rules(id),
    assessment_id INTEGER NOT NULL REFERENCES assessments(id),
    weight INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS thresholds (
    id INTEGER PRIMARY KEY,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    set_at TEXT NOT NULL
);
"""

SEED = """
INSERT INTO rules (id, condition, score_weight, state, author_id, approver_id, created_at, decided_at) VALUES
    (1, 'сумма от 400 BYN и страна не Беларусь', 40, 'действует', 2, 3, '2026-02-01T12:00:00', '2026-02-02T09:00:00'),
    (2, 'категория получателя 7995', 60, 'проект', 2, NULL, '2026-03-12T11:00:00', NULL);
INSERT INTO assessments (id, subject_type, subject_id, score, recommendation, created_at) VALUES
    (1, 'запрос аутентификации', 1, 12, 'frictionless', '2026-03-11T09:40:01'),
    (2, 'операция', 1, 18, 'пропуск', '2026-03-11T09:40:12'),
    (3, 'операция', 2, 81, 'приостановка', '2026-03-12T10:02:01');
INSERT INTO rule_hits (id, rule_id, assessment_id, weight) VALUES
    (1, 1, 3, 40);
INSERT INTO thresholds (id, amount, currency, user_id, set_at) VALUES
    (1, '200.00', 'BYN', 3, '2026-01-15T08:00:00');
"""


def ensure() -> None:
    with session(SERVICE) as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM rules").fetchone()[0]
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


def list_rules() -> list[Rule]:
    return [Rule(**dict(row)) for row in _all("SELECT * FROM rules ORDER BY id")]


def get_rule(rule_id: int) -> Rule:
    row = _one("SELECT * FROM rules WHERE id = ?", (rule_id,), f"Правило {rule_id} не найдено")
    return Rule(**dict(row))


def list_assessments() -> list[Assessment]:
    return [Assessment(**dict(row)) for row in _all("SELECT * FROM assessments ORDER BY id")]


def get_assessment(assessment_id: int) -> Assessment:
    row = _one(
        "SELECT * FROM assessments WHERE id = ?",
        (assessment_id,),
        f"Оценка риска {assessment_id} не найдена",
    )
    return Assessment(**dict(row))


def find_assessment(subject_type: str, subject_id: int) -> Assessment | None:
    ensure()
    with session(SERVICE) as connection:
        row = connection.execute(
            "SELECT * FROM assessments WHERE subject_type = ? AND subject_id = ?",
            (subject_type, subject_id),
        ).fetchone()
    if row is None:
        return None
    return Assessment(**dict(row))


def list_hits(assessment_id: int) -> list[RuleHit]:
    rows = _all(
        "SELECT * FROM rule_hits WHERE assessment_id = ? ORDER BY id",
        (assessment_id,),
    )
    return [RuleHit(**dict(row)) for row in rows]


def current_threshold() -> Threshold:
    row = _one(
        "SELECT * FROM thresholds ORDER BY set_at DESC, id DESC LIMIT 1",
        (),
        "Порог оператора не задан",
    )
    return Threshold(**dict(row))
