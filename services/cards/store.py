from shared.db import session
from shared.errors import NotFoundError

from .models import Block, Card, Client, Holder

SERVICE = "cards"

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS holders (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    full_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    holder_id INTEGER NOT NULL REFERENCES holders(id),
    masked_pan TEXT NOT NULL,
    expiry TEXT NOT NULL,
    card_type TEXT NOT NULL,
    payment_system TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS blocks (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id),
    incident_id INTEGER NOT NULL,
    decision_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    blocked_at TEXT NOT NULL
);
"""

SEED = """
INSERT INTO clients (id, name) VALUES
    (1, 'ОАО «Торгсервис»');
INSERT INTO holders (id, client_id, full_name) VALUES
    (1, 1, 'Иванов Иван Иванович'),
    (2, 1, 'Петрова Анна Сергеевна');
INSERT INTO cards (id, client_id, holder_id, masked_pan, expiry, card_type, payment_system, status) VALUES
    (1, 1, 1, '2200********1234', '2028-11', 'дебетовая', 'БЕЛКАРТ', 'действует'),
    (2, 1, 2, '9112********5678', '2027-04', 'кредитная', 'Visa', 'заблокирована');
INSERT INTO blocks (id, card_id, incident_id, decision_id, user_id, reason, blocked_at) VALUES
    (1, 2, 1, 1, 2, 'подтверждённое мошенничество', '2026-03-12T10:15:00');
"""


def ensure() -> None:
    with session(SERVICE) as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
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


def list_clients() -> list[Client]:
    return [Client(**dict(row)) for row in _all("SELECT * FROM clients ORDER BY id")]


def get_client(client_id: int) -> Client:
    row = _one("SELECT * FROM clients WHERE id = ?", (client_id,), f"Клиент {client_id} не найден")
    return Client(**dict(row))


def list_holders(client_id: int | None = None) -> list[Holder]:
    if client_id is None:
        rows = _all("SELECT * FROM holders ORDER BY id")
    else:
        rows = _all("SELECT * FROM holders WHERE client_id = ? ORDER BY id", (client_id,))
    return [Holder(**dict(row)) for row in rows]


def get_holder(holder_id: int) -> Holder:
    row = _one("SELECT * FROM holders WHERE id = ?", (holder_id,), f"Держатель {holder_id} не найден")
    return Holder(**dict(row))


def list_cards(holder_id: int | None = None) -> list[Card]:
    if holder_id is None:
        rows = _all("SELECT * FROM cards ORDER BY id")
    else:
        rows = _all("SELECT * FROM cards WHERE holder_id = ? ORDER BY id", (holder_id,))
    return [Card(**dict(row)) for row in rows]


def get_card(card_id: int) -> Card:
    row = _one("SELECT * FROM cards WHERE id = ?", (card_id,), f"Карточка {card_id} не найдена")
    return Card(**dict(row))


def list_blocks(card_id: int) -> list[Block]:
    rows = _all("SELECT * FROM blocks WHERE card_id = ? ORDER BY id", (card_id,))
    return [Block(**dict(row)) for row in rows]
