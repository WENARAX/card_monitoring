import os

HOST = os.environ.get("MONITORING_HOST", "127.0.0.1")
PORT = int(os.environ.get("MONITORING_PORT", "8080"))
