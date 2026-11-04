"""Chrome de la UI promovida a /: frontend auditado 7/7 mismo-origen.

GET / (y /app) sirve src/static/app.html: dos textareas con fetch reales,
suite tras <details>, empty state honesto ES/EN, cero CDN.
"""

import sys
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import server  # noqa: E402


class PromotedRootTest(unittest.TestCase):
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

    def _get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8")

    def test_root_y_app_sirven_los_mismos_bytes(self) -> None:
        s1, ct1, root = self._get("/")
        s2, _, app = self._get("/app")
        self.assertEqual((s1, s2), (200, 200))
        self.assertIn("text/html", ct1)
        self.assertEqual(root, app, "/ y /app deben servir el frontend auditado")
        self.assertEqual(root.encode("utf-8"), server.APP_PATH.read_bytes())

    def test_marcas_del_frontend_auditado(self) -> None:
        _, _, page = self._get("/")
        for marker in ('id="txt-extract"', 'id="txt-draft"', 'id="chips"',
                       'id="inv"', 'id="verdict"', 'id="suite-details"',
                       "/api/extract", "/api/draft", "/api/verify",
                       "tool_call_id", "performance.now"):
            with self.subTest(marker=marker):
                self.assertIn(marker, page, f"falta marca {marker}")

    def test_bilingue_real_sin_fosiles(self) -> None:
        _, _, page = self._get("/")
        self.assertIn("Sin datos", page, "falta empty state ES")
        self.assertIn("No data yet", page, "falta empty state EN")
        self.assertIn("Extraer datos trazables", page, "falta ES")
        self.assertIn("Extract traceable data", page, "falta EN")
        self.assertIn("Oculto (ejecuta la suite para auditar)", page,
                      "la suite arranca oculta")

    def test_zero_deps(self) -> None:
        _, _, page = self._get("/")
        low = page.lower()
        self.assertNotIn("tailwind", low, "nada de CDN Tailwind")
        self.assertNotIn("googleapis", low, "nada de Google Fonts")
        self.assertNotIn("<link", low, "cero links externos")
        self.assertIn("<script>", page, "el JS va inline")


if __name__ == "__main__":
    unittest.main()
