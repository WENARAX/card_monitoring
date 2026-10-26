from shared.db import session
from shared.errors import NotFoundError

from .models import AuditRecord, User

SERVICE = "access"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    login TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL,
    full_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_records (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    object_type TEXT NOT NULL,
    object_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""

SEED = """
INSERT INTO users (id, login, password_hash, role, status, full_name) VALUES
    (1, 'operator', 'sha256:not-a-password', 'оператор', 'действует', 'Сидорова Мария'),
    (2, 'analyst', 'sha256:not-a-password', 'аналитик', 'действует', 'Ковалёв Пётр'),
    (3, 'head', 'sha256:not-a-password', 'руководитель', 'действует', 'Новик Елена'),
    (4, 'admin', 'sha256:not-a-password', 'администратор', 'действует', 'Гриб Алексей');
INSERT INTO audit_records (id, user_id, action, object_type, object_id, created_at) VALUES
    (1, 3, 'утвердил правило', 'правило', 1, '2026-02-02T09:00:00');
"""


def ensure() -> None:
    with session(SERVICE) as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
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


def list_users() -> list[User]:
    return [User(**dict(row)) for row in _all("SELECT * FROM users ORDER BY id")]


def get_user(user_id: int) -> User:
    row = _one("SELECT * FROM users WHERE id = ?", (user_id,), f"Пользователь {user_id} не найден")
    return User(**dict(row))


def list_audit(user_id: int | None = None) -> list[AuditRecord]:
    if user_id is None:
        rows = _all("SELECT * FROM audit_records ORDER BY id")
    else:
        rows = _all("SELECT * FROM audit_records WHERE user_id = ? ORDER BY id", (user_id,))
    return [AuditRecord(**dict(row)) for row in rows]
