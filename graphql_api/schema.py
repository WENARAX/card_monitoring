import strawberry
from graphql import GraphQLError

from graphql_api.services import monitoring
from shared.errors import NotFoundError


def call(loader):
    try:
        return loader()
    except NotFoundError as exc:
        raise GraphQLError(str(exc)) from None


@strawberry.type
class FiredRuleType:
    id: int
    condition: str
    weight: int
    state: str

    @classmethod
    def from_dto(cls, item) -> "FiredRuleType":
        return cls(id=item.id, condition=item.condition, weight=item.weight, state=item.state)


@strawberry.type
class DecisionViewType:
    outcome: str
    comment: str
    created_at: str
    author_name: str
    author_role: str


@strawberry.type
class BlockViewType:
    reason: str
    blocked_at: str
    author_name: str
    author_role: str


@strawberry.type
class HistoryItemType:
    amount: str
    currency: str
    created_at: str
    channel_name: str
    recipient: str


@strawberry.type
class IncidentQueueItemType:
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

    @classmethod
    def from_dto(cls, item) -> "IncidentQueueItemType":
        return cls(**item.__dict__)


@strawberry.type
class OperationCardType:
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
    fired_rules: list[FiredRuleType]
    decisions: list[DecisionViewType]
    blocks: list[BlockViewType]
    history: list[HistoryItemType]

    @classmethod
    def from_dto(cls, item) -> "OperationCardType":
        return cls(
            id=item.id,
            amount=item.amount,
            currency=item.currency,
            created_at=item.created_at,
            recipient=item.recipient,
            limit_checked=item.limit_checked,
            channel_name=item.channel_name,
            country_name=item.country_name,
            category_name=item.category_name,
            masked_pan=item.masked_pan,
            card_status=item.card_status,
            payment_system=item.payment_system,
            holder_name=item.holder_name,
            client_name=item.client_name,
            auth_mode=item.auth_mode,
            auth_result=item.auth_result,
            score=item.score,
            recommendation=item.recommendation,
            fired_rules=[FiredRuleType.from_dto(rule) for rule in item.fired_rules],
            decisions=[DecisionViewType(**decision.__dict__) for decision in item.decisions],
            blocks=[BlockViewType(**block.__dict__) for block in item.blocks],
            history=[HistoryItemType(**entry.__dict__) for entry in item.history],
        )


@strawberry.type
class RuleViewType:
    id: int
    condition: str
    score_weight: int
    state: str
    created_at: str
    decided_at: str | None
    author_name: str
    approver_name: str | None

    @classmethod
    def from_dto(cls, item) -> "RuleViewType":
        return cls(**item.__dict__)


@strawberry.type
class ReportType:
    incident_count: int
    stopped_amount: str
    currency: str
    false_positive_share: str | None
    notice: str | None
    channel_name: str | None
    fired_rules: list[FiredRuleType]

    @classmethod
    def from_dto(cls, item) -> "ReportType":
        return cls(
            incident_count=item.incident_count,
            stopped_amount=item.stopped_amount,
            currency=item.currency,
            false_positive_share=item.false_positive_share,
            notice=item.notice,
            channel_name=item.channel_name,
            fired_rules=[FiredRuleType.from_dto(rule) for rule in item.fired_rules],
        )


@strawberry.type
class Query:
    @strawberry.field(description="Очередь инцидентов оператора и аналитика")
    def incident_queue(self) -> list[IncidentQueueItemType]:
        return [IncidentQueueItemType.from_dto(item) for item in monitoring.incident_queue()]

    @strawberry.field(description="Карточка операции: режим аутентификации, показатель, правила и история")
    def operation_card(self, id: int) -> OperationCardType | None:
        return call(lambda: OperationCardType.from_dto(monitoring.get_operation_card(id)))

    @strawberry.field(description="Правила оценки: проект, действующее и отклонённое")
    def rules(self) -> list[RuleViewType]:
        return [RuleViewType.from_dto(item) for item in monitoring.list_rules()]

    @strawberry.field
    def rule(self, id: int) -> RuleViewType | None:
        return call(lambda: RuleViewType.from_dto(monitoring.get_rule(id)))

    @strawberry.field(description="Отчёт руководителя по решениям. Отдельной таблицы отчёта нет")
    def report(self, channel_code: str | None = None) -> ReportType:
        return call(lambda: ReportType.from_dto(monitoring.build_report(channel_code)))


schema = strawberry.Schema(query=Query)
