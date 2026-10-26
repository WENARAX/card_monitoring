import os
import tempfile
import unittest
from pathlib import Path

os.environ["MONITORING_DATA"] = tempfile.mkdtemp(prefix="monitoring-")

from graphql_api.schema import schema  # noqa: E402


def run(query: str):
    return schema.execute_sync(query)


class ReadApiTest(unittest.TestCase):
    def test_operation_card_joins_auth_and_parties(self) -> None:
        result = run(
            """
            {
              operationCard(id: 1) {
                amount
                recipient
                limitChecked
                authMode
                authResult
                channelName
                categoryName
                maskedPan
                holderName
                clientName
                recommendation
                firedRules { state }
                decisions { outcome }
              }
            }
            """
        )
        self.assertIsNone(result.errors, result.errors)
        card = result.data["operationCard"]
        self.assertEqual(card["amount"], "86.40")
        self.assertEqual(card["authMode"], "frictionless")
        self.assertEqual(card["channelName"], "интернет")
        self.assertEqual(card["categoryName"], "продукты")
        self.assertEqual(card["maskedPan"], "2200********1234")
        self.assertEqual(card["holderName"], "Иванов Иван Иванович")
        self.assertEqual(card["recommendation"], "пропуск")
        self.assertEqual(card["firedRules"], [])
        self.assertEqual(card["decisions"], [])

    def test_queue_and_blocked_card(self) -> None:
        result = run(
            """
            {
              incidentQueue {
                status
                amount
                channelName
                maskedPan
                recommendation
              }
              operationCard(id: 2) {
                authMode
                categoryName
                recommendation
                firedRules { condition weight }
                decisions { outcome authorRole }
                blocks { reason authorRole }
              }
            }
            """
        )
        self.assertIsNone(result.errors, result.errors)
        item = result.data["incidentQueue"][0]
        self.assertEqual(item["channelName"], "банкомат")
        self.assertEqual(item["amount"], "500.00")
        self.assertEqual(item["maskedPan"], "9112********5678")
        card = result.data["operationCard"]
        self.assertIsNone(card["authMode"])
        self.assertIsNone(card["categoryName"])
        self.assertEqual(card["recommendation"], "приостановка")
        self.assertEqual(card["firedRules"][0]["weight"], 40)
        self.assertEqual(card["decisions"][0]["authorRole"], "аналитик")
        self.assertEqual(card["blocks"][0]["reason"], "подтверждённое мошенничество")

    def test_missing_operation_is_an_error(self) -> None:
        result = run("{ operationCard(id: 99) { id } }")
        self.assertIsNone(result.data["operationCard"])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("не найдена", result.errors[0].message)

    def test_rules_and_report_are_not_tables(self) -> None:
        result = run(
            """
            {
              rule(id: 2) { state approverName }
              rules { state }
              report { incidentCount stoppedAmount falsePositiveShare notice firedRules { id } }
              reportInternet: report(channelCode: "internet") { incidentCount notice }
            }
            """
        )
        self.assertIsNone(result.errors, result.errors)
        self.assertEqual(result.data["rule"]["state"], "проект")
        self.assertIsNone(result.data["rule"]["approverName"])
        self.assertEqual(
            {item["state"] for item in result.data["rules"]},
            {"действует", "проект"},
        )
        report = result.data["report"]
        self.assertEqual(report["incidentCount"], 1)
        self.assertEqual(report["stoppedAmount"], "500.00")
        self.assertEqual(report["falsePositiveShare"], "0.00")
        self.assertIsNone(report["notice"])
        self.assertEqual(report["firedRules"][0]["id"], 1)
        self.assertEqual(result.data["reportInternet"]["notice"], "За период нет инцидентов")
        self.assertNotIn("password", str(result.data))

    def test_schema_has_no_table_roots(self) -> None:
        result = run("{ __schema { queryType { fields { name } } } }")
        names = {field["name"] for field in result.data["__schema"]["queryType"]["fields"]}
        self.assertEqual(
            names,
            {"incidentQueue", "operationCard", "rules", "rule", "report"},
        )

    def test_databases_do_not_store_full_pan(self) -> None:
        root = Path(os.environ["MONITORING_DATA"])
        for path in root.glob("*/*.db"):
            text = path.read_bytes().decode("utf-8", errors="ignore")
            self.assertNotRegex(text, r"\d{16}")


if __name__ == "__main__":
    unittest.main()
