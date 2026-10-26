import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from graphql_api.config import HOST, PORT
from graphql_api.schema import schema


class GraphQLHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/graphql":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._write(400, {"errors": [{"message": "Тело запроса не является JSON"}]})
            return
        result = schema.execute_sync(body.get("query", ""), variable_values=body.get("variables"))
        payload: dict = {"data": result.data}
        if result.errors:
            payload["errors"] = [{"message": error.message} for error in result.errors]
        self._write(200, payload)

    def _write(self, status: int, payload: dict) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args) -> None:
        print(fmt % args)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), GraphQLHandler)
    print(f"GraphQL API: http://{HOST}:{PORT}/graphql", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
