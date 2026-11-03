"""Demo web Kreo Fiscal Shield: planner mock + gate determinista real.

Solo stdlib. Endpoints:
  GET  /         pagina demo (dos casos: PASS y BLOQUEADO)
  GET  /health   chequeo Coolify
  POST /api/verify  {"amounts":[{"cents":int,"tool_call_id":str?}],"dian_schema_ok":bool}
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from verify import verify_draft

PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kreo Fiscal Shield — demo Meta hackathon</title>
<style>body{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem}
button{padding:.6rem 1rem;margin:.3rem;font-size:1rem}pre{background:#f4f4f4;padding:1rem;white-space:pre-wrap}</style>
</head><body>
<h1>Kreo Fiscal Shield</h1>
<p>El modelo propone, el <b>verifier</b> decide. Sin <code>tool_call_id</code> no hay transmit.</p>
<button onclick="run(true)">Caso 1: borrador valido</button>
<button onclick="run(false)">Caso 2: cifra sin tool_call_id</button>
<pre id="out">pulsa un caso…</pre>
<script>
async function run(ok){
  const body = ok
    ? {amounts:[{cents:245000000,tool_call_id:"call_demo_1",concept:"servicio"}],dian_schema_ok:true}
    : {amounts:[{cents:245000000,concept:"servicio"}],dian_schema_ok:true};
  const r = await fetch("/api/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  document.getElementById("out").textContent = JSON.stringify(await r.json(), null, 2);
}
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    server_version = "FiscalShield/1.0"

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, b'{"ok":true}')
        elif self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/verify":
            self._send(404, b'{"error":"not found"}')
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        try:
            draft = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, b'{"transmit":false,"veredicto":"bloqueado: JSON invalido"}')
            return
        if not isinstance(draft, dict):
            self._send(400, b'{"transmit":false,"veredicto":"bloqueado: cuerpo invalido"}')
            return
        ok, msg = verify_draft(draft)
        self._send(200 if ok else 422, json.dumps({"transmit": ok, "veredicto": msg}).encode("utf-8"))

    def log_message(self, *args: object) -> None:
        pass


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"fiscal-shield demo en puerto {port} (mock local)")
    server.serve_forever()


if __name__ == "__main__":
    main()
