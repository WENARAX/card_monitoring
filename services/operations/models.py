from dataclasses import dataclass


@dataclass(frozen=True)
class DictionaryItem:
    id: int
    code: str
    name: str


@dataclass(frozen=True)
class AuthRequest:
    id: int
    card_id: int
    amount: str
    currency: str
    mode: str
    result: str
    device_summary: str
    merchant_summary: str
    external_verdict: str | None
    created_at: str


@dataclass(frozen=True)
class Operation:
    id: int
    card_id: int
    auth_request_id: int | None
    channel_id: int
    country_id: int
    category_id: int | None
    amount: str
    currency: str
    recipient: str
    limit_checked: int
    created_at: str
