from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    id: int
    condition: str
    score_weight: int
    state: str
    author_id: int
    approver_id: int | None
    created_at: str
    decided_at: str | None


@dataclass(frozen=True)
class Assessment:
    id: int
    subject_type: str
    subject_id: int
    score: int
    recommendation: str
    created_at: str


@dataclass(frozen=True)
class RuleHit:
    id: int
    rule_id: int
    assessment_id: int
    weight: int


@dataclass(frozen=True)
class Threshold:
    id: int
    amount: str
    currency: str
    user_id: int
    set_at: str
