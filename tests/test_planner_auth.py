"""Permanent regression for Meta 401 (2026-11-04).

Root cause: the META_SPARK_API_KEY value stored in Coolify carried literal
wrapping quotes; the header went out as Bearer "<key>" and Meta answered
401 invalid_api_key only from inside containers.

These tests require a key with wrapping quotes (or CR/LF) to authenticate
just like the clean key, without using any real secret: the "Meta" in the
integration test is a fake local HTTP server that records the received
Authorization header. Counts-only: no value is ever printed.

Run: python3 -m unittest discover -s tests -v
"""

import json
import os
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402

FAKE_KEY = "sk-fake-regression-key-0001"


class SanitizeApiKeyTest(unittest.TestCase):
    def test_strips_wrapping_double_quotes(self) -> None:
        self.assertEqual(server.sanitize_api_key(f'"{FAKE_KEY}"'), FAKE_KEY)

    def test_strips_wrapping_single_quotes(self) -> None:
        self.assertEqual(server.sanitize_api_key(f"'{FAKE_KEY}'"), FAKE_KEY)

    def test_strips_cr_lf_and_surrounding_spaces(self) -> None:
        self.assertEqual(server.sanitize_api_key(f'  "{FAKE_KEY}"\r\n'), FAKE_KEY)

    def test_clean_key_is_unchanged(self) -> None:
        self.assertEqual(server.sanitize_api_key(FAKE_KEY), FAKE_KEY)


class _FakeMetaHandler(BaseHTTPRequestHandler):
    received_authorization = ""

    def do_POST(self):  # noqa: N802
        type(self).received_authorization = self.headers.get("Authorization", "")
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_regression_1",
                                "function": {
                                    "name": "extract_business_fields",
                                    "arguments": json.dumps(
                                        {"company_name": "Comercial Andina SAS", "monthly_invoices": 120}
                                    ),
                                },
                            }
                        ]
                    }
                }
            ]
        }
        raw = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args: object) -> None:
        pass


class QuotedKeyAuthenticatesTest(unittest.TestCase):
    def test_key_with_wrapping_quotes_authenticates(self) -> None:
        fake = ThreadingHTTPServer(("127.0.0.1", 0), _FakeMetaHandler)
        thread = threading.Thread(target=fake.serve_forever, daemon=True)
        thread.start()
        try:
            env = {
                "META_SPARK_PLANNER_ENDPOINT": f"http://127.0.0.1:{fake.server_port}/v1/chat/completions",
                "META_SPARK_API_KEY": f'"{FAKE_KEY}"',
                "META_SPARK_PLANNER_MODEL": "muse-spark-1.3",
            }
            with mock.patch.dict(os.environ, env):
                result = server.meta_planner_fields(
                    "Mi empresa es Comercial Andina SAS, emitimos 120 facturas al mes"
                )
        finally:
            fake.shutdown()
            fake.server_close()

        self.assertIsNotNone(result, "el planner degrado pese a que la clave sanitizada es valida")
        self.assertEqual(
            _FakeMetaHandler.received_authorization,
            f"Bearer {FAKE_KEY}",
            "el header Authorization debe llevar la clave sin comillas envolventes",
        )
        self.assertEqual(result["tool_call_id"], "call_regression_1")
        self.assertIn("Muse Spark", result["source"])


if __name__ == "__main__":
    unittest.main()
