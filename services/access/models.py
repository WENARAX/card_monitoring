from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    login: str
    password_hash: str
    role: str
    status: str
    full_name: str


@dataclass(frozen=True)
class AuditRecord:
    id: int
    user_id: int
    action: str
    object_type: str
    object_id: int
    created_at: str
