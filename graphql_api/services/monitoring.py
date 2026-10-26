"""Сборка ответов для сценариев из записки. К таблицам сервисов этот модуль не обращается."""

from dataclasses import dataclass
from decimal import Decimal

from graphql_api.clients.mocks import build_clients
from shared.errors import NotFoundError

CLIENTS = build_clients()
STOPPED = {"приостановка", "отклонение", "отказ"}


@dataclass(frozen=True)
class FiredRule:
    id: int
    condition: str
    weight: int
    state: str


@dataclass(frozen=True)
class DecisionView:
    outcome: str
    comment: str
    created_at: str
    author_name: str
    author_role: str


@dataclass(frozen=True)
class BlockView:
    reason: str
    blocked_at: str
    author_name: str
    author_role: str


@dataclass(frozen=True)
class HistoryItem:
    amount: str
    currency: str
    created_at: str
    channel_name: str
    recipient: str


@dataclass(frozen=True)
class IncidentQueueItem:
    id: int
    status: str
    detected_at: str
    amount: str
    currency: str
    channel_name: str
    recipient: str
    score: int
    recommendation: str
    masked_pan: str


@dataclass(frozen=True)
class OperationCard:
    id: int
    amount: str
    currency: str
    created_at: str
    recipient: str
    limit_checked: bool
    channel_name: str
    country_name: str
    category_name: str | None
    masked_pan: str
    card_status: str
    payment_system: str
    holder_name: str
    client_name: str
    auth_mode: str | None
    auth_result: str | None
    score: int
    recommendation: str
    fired_rules: list[FiredRule]
    decisions: list[DecisionView]
    blocks: list[BlockView]
    history: list[HistoryItem]


@dataclass(frozen=True)
class RuleView:
    id: int
    condition: str
    score_weight: int
    state: str
    created_at: str
    decided_at: str | None
    author_name: str
    approver_name: str | None


@dataclass(frozen=True)
class Report:
    incident_count: int
    stopped_amount: str
    currency: str
    false_positive_share: str | None
    notice: str | None
    channel_name: str | None
    fired_rules: list[FiredRule]


def incident_queue() -> list[IncidentQueueItem]:
    items = []
    for incident in CLIENTS.incidents.list_incidents():
        facts = _incident_facts(incident)
        items.append(
            IncidentQueueItem(
                id=incident.id,
                status=incident.status,
                detected_at=incident.detected_at,
                amount=facts["amount"],
                currency=facts["currency"],
                channel_name=facts["channel_name"],
                recipient=facts["recipient"],
                score=facts["assessment"].score,
                recommendation=facts["assessment"].recommendation,
                masked_pan=facts["card"].masked_pan,
            )
        )
    return items


def get_operation_card(operation_id: int) -> OperationCard:
    operation = CLIENTS.operations.get_operation(operation_id)
    card = CLIENTS.cards.get_card(operation.card_id)
    holder = CLIENTS.cards.get_holder(card.holder_id)
    client = CLIENTS.cards.get_client(card.client_id)
    channel = CLIENTS.operations.get_channel(operation.channel_id)
    country = CLIENTS.operations.get_country(operation.country_id)
    category = (
        CLIENTS.operations.get_category(operation.category_id)
        if operation.category_id is not None
        else None
    )
    auth_mode = None
    auth_result = None
    if operation.auth_request_id is not None:
        auth_request = CLIENTS.operations.get_auth_request(operation.auth_request_id)
        auth_mode = auth_request.mode
        auth_result = auth_request.result
    assessment = CLIENTS.risk.find_assessment("операция", operation.id)
    if assessment is None:
        raise NotFoundError(f"Оценка операции {operation.id} не найдена")
    incident = _incident_for_assessment(assessment.id)
    decisions = _decision_views(incident.id) if incident is not None else []
    return OperationCard(
        id=operation.id,
        amount=operation.amount,
        currency=operation.currency,
        created_at=operation.created_at,
        recipient=operation.recipient,
        limit_checked=bool(operation.limit_checked),
        channel_name=channel.name,
        country_name=country.name,
        category_name=category.name if category is not None else None,
        masked_pan=card.masked_pan,
        card_status=card.status,
        payment_system=card.payment_system,
        holder_name=holder.full_name,
        client_name=client.name,
        auth_mode=auth_mode,
        auth_result=auth_result,
        score=assessment.score,
        recommendation=assessment.recommendation,
        fired_rules=_fired_rules(assessment.id),
        decisions=decisions,
        blocks=_block_views(card.id),
        history=_history(card.id, operation.id),
    )


def list_rules() -> list[RuleView]:
    return [_rule_view(item) for item in CLIENTS.risk.list_rules()]


def get_rule(rule_id: int) -> RuleView:
    return _rule_view(CLIENTS.risk.get_rule(rule_id))


def build_report(channel_code: str | None = None) -> Report:
    channel_name = None
    if channel_code is not None:
        channel_name = _channel_by_code(channel_code).name
    included = []
    for incident in CLIENTS.incidents.list_incidents():
        facts = _incident_facts(incident)
        if channel_name is not None and facts["channel_name"] != channel_name:
            continue
        included.append((incident, facts))
    if not included:
        return Report(
            incident_count=0,
            stopped_amount="0.00",
            currency="BYN",
            false_positive_share=None,
            notice="За период нет инцидентов",
            channel_name=channel_name,
            fired_rules=[],
        )
    false_count = sum(1 for incident, _facts in included if incident.status == "ложное срабатывание")
    stopped = Decimal("0.00")
    currency = included[0][1]["currency"]
    fired: dict[int, FiredRule] = {}
    for incident, facts in included:
        if incident.status != "ложное срабатывание" and facts["assessment"].recommendation in STOPPED:
            stopped += Decimal(facts["amount"])
        for rule in _fired_rules(facts["assessment"].id):
            fired[rule.id] = rule
    share = (Decimal(false_count) / Decimal(len(included))).quantize(Decimal("0.01"))
    return Report(
        incident_count=len(included),
        stopped_amount=f"{stopped.quantize(Decimal('0.01'))}",
        currency=currency,
        false_positive_share=f"{share}",
        notice=None,
        channel_name=channel_name,
        fired_rules=list(fired.values()),
    )


def _incident_facts(incident) -> dict:
    assessment = CLIENTS.risk.get_assessment(incident.assessment_id)
    if assessment.subject_type == "операция":
        operation = CLIENTS.operations.get_operation(assessment.subject_id)
        channel = CLIENTS.operations.get_channel(operation.channel_id)
        card = CLIENTS.cards.get_card(operation.card_id)
        return {
            "assessment": assessment,
            "amount": operation.amount,
            "currency": operation.currency,
            "channel_name": channel.name,
            "recipient": operation.recipient,
            "card": card,
        }
    if assessment.subject_type == "запрос аутентификации":
        request = CLIENTS.operations.get_auth_request(assessment.subject_id)
        card = CLIENTS.cards.get_card(request.card_id)
        return {
            "assessment": assessment,
            "amount": request.amount,
            "currency": request.currency,
            "channel_name": "интернет",
            "recipient": request.merchant_summary,
            "card": card,
        }
    raise NotFoundError(f"Оценка {assessment.id} не связана с операцией или запросом аутентификации")


def _incident_for_assessment(assessment_id: int):
    for incident in CLIENTS.incidents.list_incidents():
        if incident.assessment_id == assessment_id:
            return incident
    return None


def _fired_rules(assessment_id: int) -> list[FiredRule]:
    rules = []
    for hit in CLIENTS.risk.list_hits(assessment_id):
        rule = CLIENTS.risk.get_rule(hit.rule_id)
        rules.append(FiredRule(id=rule.id, condition=rule.condition, weight=hit.weight, state=rule.state))
    return rules


def _decision_views(incident_id: int) -> list[DecisionView]:
    views = []
    for decision in CLIENTS.incidents.list_decisions(incident_id):
        author = CLIENTS.access.get_user(decision.user_id)
        views.append(
            DecisionView(
                outcome=decision.outcome,
                comment=decision.comment,
                created_at=decision.created_at,
                author_name=author.full_name,
                author_role=author.role,
            )
        )
    return views


def _block_views(card_id: int) -> list[BlockView]:
    views = []
    for block in CLIENTS.cards.list_blocks(card_id):
        author = CLIENTS.access.get_user(block.user_id)
        views.append(
            BlockView(
                reason=block.reason,
                blocked_at=block.blocked_at,
                author_name=author.full_name,
                author_role=author.role,
            )
        )
    return views


def _history(card_id: int, current_operation_id: int) -> list[HistoryItem]:
    items = []
    for operation in CLIENTS.operations.list_operations():
        if operation.card_id != card_id or operation.id == current_operation_id:
            continue
        channel = CLIENTS.operations.get_channel(operation.channel_id)
        items.append(
            HistoryItem(
                amount=operation.amount,
                currency=operation.currency,
                created_at=operation.created_at,
                channel_name=channel.name,
                recipient=operation.recipient,
            )
        )
    return items


def _rule_view(rule) -> RuleView:
    author = CLIENTS.access.get_user(rule.author_id)
    approver_name = None
    if rule.approver_id is not None:
        approver_name = CLIENTS.access.get_user(rule.approver_id).full_name
    return RuleView(
        id=rule.id,
        condition=rule.condition,
        score_weight=rule.score_weight,
        state=rule.state,
        created_at=rule.created_at,
        decided_at=rule.decided_at,
        author_name=author.full_name,
        approver_name=approver_name,
    )


def _channel_by_code(code: str):
    for channel in CLIENTS.operations.list_channels():
        if channel.code == code:
            return channel
    raise NotFoundError(f"Канал {code} не найден")

