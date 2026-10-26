from shared.db import session
from shared.errors import NotFoundError

from .models import AuthRequest, DictionaryItem, Operation

SERVICE = "operations"

SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_requests (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL,
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    mode TEXT NOT NULL,
    result TEXT NOT NULL,
    device_summary TEXT NOT NULL,
    merchant_summary TEXT NOT NULL,
    external_verdict TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS operations (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL,
    auth_request_id INTEGER REFERENCES auth_requests(id),
    channel_id INTEGER NOT NULL REFERENCES channels(id),
    country_id INTEGER NOT NULL REFERENCES countries(id),
    category_id INTEGER REFERENCES categories(id),
    amount TEXT NOT NULL,
    currency TEXT NOT NULL,
    recipient TEXT NOT NULL,
    limit_checked INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""

SEED = """
INSERT INTO channels (id, code, name) VALUES
    (1, 'internet', 'интернет'),
    (2, 'pos', 'терминал'),
    (3, 'atm', 'банкомат'),
    (4, 'transfer', 'перевод');
INSERT INTO countries (id, code, name) VALUES
    (1, 'BY', 'Беларусь'),
    (2, 'PL', 'Польша');
INSERT INTO categories (id, code, name) VALUES
    (1, '5411', 'продукты'),
    (2, '7995', 'азартные игры');
INSERT INTO auth_requests (
    id, card_id, amount, currency, mode, result, device_summary, merchant_summary, external_verdict, created_at
) VALUES (
    1, 1, '86.40', 'BYN', 'frictionless', 'успех',
    'браузер Chrome, устройство уже встречалось',
    'учётная запись магазина старше года',
    'низкий риск платёжной системы',
    '2026-03-11T09:40:00'
);
INSERT INTO operations (
    id, card_id, auth_request_id, channel_id, country_id, category_id,
    amount, currency, recipient, limit_checked, created_at
) VALUES
    (1, 1, 1, 1, 1, 1, '86.40', 'BYN', 'Магазин «Соседи»', 1, '2026-03-11T09:40:12'),
    (2, 2, NULL, 3, 2, NULL, '500.00', 'BYN', 'Банкомат, Варшава', 1, '2026-03-12T10:02:00');
"""


def ensure() -> None:
    with session(SERVICE) as connection:
        connection.executescript(SCHEMA)
        count = connection.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
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


def _dict_items(table: str) -> list[DictionaryItem]:
    return [DictionaryItem(**dict(row)) for row in _all(f"SELECT * FROM {table} ORDER BY id")]


def list_channels() -> list[DictionaryItem]:
    return _dict_items("channels")


def get_channel(item_id: int) -> DictionaryItem:
    row = _one("SELECT * FROM channels WHERE id = ?", (item_id,), f"Канал {item_id} не найден")
    return DictionaryItem(**dict(row))


def list_countries() -> list[DictionaryItem]:
    return _dict_items("countries")


def get_country(item_id: int) -> DictionaryItem:
    row = _one("SELECT * FROM countries WHERE id = ?", (item_id,), f"Страна {item_id} не найдена")
    return DictionaryItem(**dict(row))


def list_categories() -> list[DictionaryItem]:
    return _dict_items("categories")


def get_category(item_id: int) -> DictionaryItem:
    row = _one(
        "SELECT * FROM categories WHERE id = ?",
        (item_id,),
        f"Категория получателя {item_id} не найдена",
    )
    return DictionaryItem(**dict(row))


def list_auth_requests() -> list[AuthRequest]:
    return [AuthRequest(**dict(row)) for row in _all("SELECT * FROM auth_requests ORDER BY id")]


def get_auth_request(request_id: int) -> AuthRequest:
    row = _one(
        "SELECT * FROM auth_requests WHERE id = ?",
        (request_id,),
        f"Запрос аутентификации {request_id} не найден",
    )
    return AuthRequest(**dict(row))


def find_operation_by_auth_request(request_id: int) -> Operation | None:
    ensure()
    with session(SERVICE) as connection:
        row = connection.execute(
            "SELECT * FROM operations WHERE auth_request_id = ?",
            (request_id,),
        ).fetchone()
    if row is None:
        return None
    return Operation(**dict(row))


def list_operations() -> list[Operation]:
    return [Operation(**dict(row)) for row in _all("SELECT * FROM operations ORDER BY id")]


def get_operation(operation_id: int) -> Operation:
    row = _one(
        "SELECT * FROM operations WHERE id = ?",
        (operation_id,),
        f"Операция {operation_id} не найдена",
    )
    return Operation(**dict(row))
