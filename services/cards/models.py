from dataclasses import dataclass


@dataclass(frozen=True)
class Client:
    id: int
    name: str


@dataclass(frozen=True)
class Holder:
    id: int
    client_id: int
    full_name: str


@dataclass(frozen=True)
class Card:
    id: int
    client_id: int
    holder_id: int
    masked_pan: str
    expiry: str
    card_type: str
    payment_system: str
    status: str


@dataclass(frozen=True)
class Block:
    id: int
    card_id: int
    incident_id: int
    decision_id: int
    user_id: int
    reason: str
    blocked_at: str
