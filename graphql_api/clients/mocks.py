"""Mock стоит на месте будущего gRPC-клиента и вызывает сервис в этом же процессе."""

from services.access import store as access_store
from services.cards import store as cards_store
from services.incidents import store as incidents_store
from services.operations import store as operations_store
from services.risk import store as risk_store


class MockCardsClient:
    def list_clients(self):
        return cards_store.list_clients()

    def get_client(self, client_id: int):
        return cards_store.get_client(client_id)

    def list_holders(self, client_id: int | None = None):
        return cards_store.list_holders(client_id)

    def get_holder(self, holder_id: int):
        return cards_store.get_holder(holder_id)

    def list_cards(self, holder_id: int | None = None):
        return cards_store.list_cards(holder_id)

    def get_card(self, card_id: int):
        return cards_store.get_card(card_id)

    def list_blocks(self, card_id: int):
        return cards_store.list_blocks(card_id)


class MockOperationsClient:
    def list_channels(self):
        return operations_store.list_channels()

    def get_channel(self, item_id: int):
        return operations_store.get_channel(item_id)

    def list_countries(self):
        return operations_store.list_countries()

    def get_country(self, item_id: int):
        return operations_store.get_country(item_id)

    def list_categories(self):
        return operations_store.list_categories()

    def get_category(self, item_id: int):
        return operations_store.get_category(item_id)

    def list_auth_requests(self):
        return operations_store.list_auth_requests()

    def get_auth_request(self, request_id: int):
        return operations_store.get_auth_request(request_id)

    def find_operation_by_auth_request(self, request_id: int):
        return operations_store.find_operation_by_auth_request(request_id)

    def list_operations(self):
        return operations_store.list_operations()

    def get_operation(self, operation_id: int):
        return operations_store.get_operation(operation_id)


class MockRiskClient:
    def list_rules(self):
        return risk_store.list_rules()

    def get_rule(self, rule_id: int):
        return risk_store.get_rule(rule_id)

    def list_assessments(self):
        return risk_store.list_assessments()

    def get_assessment(self, assessment_id: int):
        return risk_store.get_assessment(assessment_id)

    def find_assessment(self, subject_type: str, subject_id: int):
        return risk_store.find_assessment(subject_type, subject_id)

    def list_hits(self, assessment_id: int):
        return risk_store.list_hits(assessment_id)

    def current_threshold(self):
        return risk_store.current_threshold()


class MockIncidentsClient:
    def list_incidents(self):
        return incidents_store.list_incidents()

    def get_incident(self, incident_id: int):
        return incidents_store.get_incident(incident_id)

    def list_decisions(self, incident_id: int):
        return incidents_store.list_decisions(incident_id)

    def get_decision(self, decision_id: int):
        return incidents_store.get_decision(decision_id)


class MockAccessClient:
    def list_users(self):
        return access_store.list_users()

    def get_user(self, user_id: int):
        return access_store.get_user(user_id)

    def list_audit(self, user_id: int | None = None):
        return access_store.list_audit(user_id)


class Clients:
    def __init__(self) -> None:
        self.cards = MockCardsClient()
        self.operations = MockOperationsClient()
        self.risk = MockRiskClient()
        self.incidents = MockIncidentsClient()
        self.access = MockAccessClient()


def build_clients() -> Clients:
    return Clients()
