from dataclasses import dataclass


@dataclass(frozen=True)
class Incident:
    id: int
    assessment_id: int
    status: str
    detected_at: str


@dataclass(frozen=True)
class Decision:
    id: int
    incident_id: int
    user_id: int
    outcome: str
    comment: str
    created_at: str
