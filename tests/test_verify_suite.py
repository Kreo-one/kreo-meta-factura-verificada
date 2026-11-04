"""Deterministic 20-case suite + HTTP contract (P4).

Promoted from /tmp/suite20.py to a maintained test: the same 20 jobs from
the report (8 valid + 6 no-tool + 3 broken schema + 2 invalid types +
1 extract) against the real gate and the real HTTP server.
"""

import json
import math
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402
from verify import verify_draft


def build_jobs():
    """Los 20 jobs exactos del informe: (kind, body, expect_transmit)."""
    jobs = []
    for i, cents in enumerate([10000000, 245000000, 500000, 120000000,
                               35000000, 9500000, 1000, 46550000]):
        jobs.append(("verify",
                     {"amounts": [{"cents": cents, "tool_call_id": f"call_suite_{i + 1}"}],
                      "dian_schema_ok": True}, True))
    for cents in [1, 1000, 9500000, 245000000, 30000000, 10000000]:
        jobs.append(("verify", {"amounts": [{"cents": cents}], "dian_schema_ok": True}, False))
    for _ in range(3):
        jobs.append(("verify",
                     {"amounts": [{"cents": 245000000, "tool_call_id": "call_suite_valid"}],
                      "dian_schema_ok": False}, False))
    jobs.append(("verify",
                 {"amounts": [{"cents": "2450000", "tool_call_id": "call_invalid_str"}],
                  "dian_schema_ok": True}, False))
    jobs.append(("verify",
                 {"amounts": [{"cents": 24.5, "tool_call_id": "call_invalid_float"}],
                  "dian_schema_ok": True}, False))
    jobs.append(("extract",
                 {"text": "Mi empresa Distribuciones Bolivar SAS tiene 95 facturas"}, True))
    return jobs


class GateSuite20Test(unittest.TestCase):
    def test_los_20_casos_cumplen_su_expectativa(self) -> None:
        jobs = build_jobs()
        self.assertEqual(len(jobs), 20, "la suite debe tener exactamente 20 jobs")
        for n, (kind, body, expect) in enumerate(jobs, 1):
            with self.subTest(job=n, kind=kind):
                if kind == "verify":
                    transmit, _ = verify_draft(body)
                    self.assertIs(transmit, expect, f"job #{n} no cumple su expectativa")
                else:
                    fields = server.extract_business(body["text"])["fields"]
                    trazados = sum(1 for f in fields if f.get("tool_call_id"))
                    self.assertEqual(trazados, 2, f"job #{n}: extract debe dar 2/2 trazados")


class P95FormulaTest(unittest.TestCase):
    def test_indice_p95_canonico_para_n20(self) -> None:
        self.assertEqual(math.ceil(0.95 * 20) - 1, 18, "p95 de N=20 es el indice 18")


class HttpContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _post(self, path, body):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_health_ok(self) -> None:
        with urllib.request.urlopen(self.base + "/health", timeout=5) as r:
            self.assertEqual(json.loads(r.read().decode()), {"ok": True})

    def test_verify_ok_devuelve_200_y_transmite(self) -> None:
        code, data = self._post("/api/verify", {
            "amounts": [{"cents": 245000000, "tool_call_id": "call_demo_1"}],
            "dian_schema_ok": True})
        self.assertEqual(code, 200)
        self.assertTrue(data["transmit"])

    def test_verify_sin_tool_devuelve_422_y_bloquea(self) -> None:
        code, data = self._post("/api/verify", {
            "amounts": [{"cents": 245000000}], "dian_schema_ok": True})
        self.assertEqual(code, 422, "el gate bloqueado responde 422")
        self.assertFalse(data["transmit"])

    def test_extract_devuelve_2_de_2_trazados(self) -> None:
        code, data = self._post("/api/extract", {
            "text": "Mi empresa Distribuciones Bolivar SAS tiene 95 facturas"})
        self.assertEqual(code, 200)
        self.assertEqual(len(data["fields"]), 2)
        self.assertTrue(all(f.get("tool_call_id") for f in data["fields"]))

    def test_draft_ok_transmite_y_sabotaje_bloquea(self) -> None:
        text = "factura a Distribuciones Bolivar por 2.450.000 + IVA por servicios contables"
        code, data = self._post("/api/draft", {"text": text, "with_tools": True})
        self.assertEqual(code, 200)
        self.assertTrue(data["transmit"])
        self.assertIn("total_cents", data["draft"])
        code, data = self._post("/api/draft", {"text": text, "with_tools": False})
        self.assertEqual(code, 200)
        self.assertFalse(data["transmit"], "sin tool_call_id no hay transmit")

    def test_app_sirve_frontend_auditado_mismo_origen(self) -> None:
        with urllib.request.urlopen(self.base + "/app", timeout=5) as r:
            self.assertEqual(r.status, 200)
            self.assertIn("text/html", r.headers.get("Content-Type", ""))
            page = r.read().decode("utf-8")
        for marker in ('id="txt-extract"', 'id="suite-details"', "/api/draft",
                       "/api/verify", "/api/extract"):
            self.assertIn(marker, page, f"GET /app sin marca {marker}")


if __name__ == "__main__":
    unittest.main()
