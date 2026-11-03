"""Demo web Kreo Fiscal Shield: planner mock + gate determinista real.

Solo stdlib. Endpoints:
  GET  /         pagina demo (flujo: texto -> borrador -> veredicto)
  GET  /health   chequeo Coolify
  POST /api/verify  {"amounts":[...],"dian_schema_ok":bool} -> veredicto (contrato estable)
  POST /api/draft   {"text":str,"with_tools":bool} -> borrador + veredicto
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from verify import verify_draft

IVA_RATE = 19

PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kreo.One — ERP SaaS agentico: Fiscal Shield en vivo</title>
<style>
body{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;color:#1a1a1a}
textarea{width:100%;height:3.2rem;font-size:1rem;padding:.5rem}
button{padding:.6rem 1rem;margin:.4rem .2rem;font-size:1rem;cursor:pointer}
.inv{border:1px solid #ccc;border-radius:8px;padding:1rem;margin-top:1rem}
.inv table{width:100%;border-collapse:collapse}
.inv td,.inv th{border-bottom:1px solid #eee;padding:.35rem;text-align:right}
.inv td:first-child,.inv th:first-child{text-align:left}
.pass{background:#e6f7e6;border:1px solid #2c7a2c;padding:.7rem;border-radius:6px;margin-top:1rem}
.block{background:#fde8e8;border:1px solid #a33;padding:.7rem;border-radius:6px;margin-top:1rem}
.mut{font-size:.8rem;color:#666}
.tag{font-family:monospace;font-size:.8rem;background:#eee;padding:.1rem .3rem;border-radius:4px}
pre{background:#f4f4f4;padding:1rem;white-space:pre-wrap;font-size:.85rem}
</style>
</head><body>
<h1>Kreo Fiscal Shield — demo en vivo</h1>
<p>Escribe la factura en lenguaje natural. El <b>planner</b> propone, el <b>verifier</b> decide.
Sin <code>tool_call_id</code> no hay transmit. <span class="mut">(planner mock local; con la key de Meta usa el modelo real — el gate no cambia)</span></p>
<textarea id="t">factura a Distribuciones Bolivar por 2.450.000 + IVA por servicios contables</textarea><br>
<button onclick="run(true)">Generar borrador (planner con herramientas)</button>
<button onclick="run(false)">Simular LLM sin herramientas</button>
<div id="out"><p class="mut">El borrador y el veredicto aparecen aqui…</p></div>
<script>
const fmt = c => "$ " + (c/100).toLocaleString("es-CO");
async function run(withTools){
  const r = await fetch("/api/draft",{method:"POST",headers:{"Content-Type":"application/json"},
    body: JSON.stringify({text: document.getElementById("t").value, with_tools: withTools})});
  const d = await r.json();
  const items = d.draft.items.map(it =>
    `<tr><td>${it.concept} ${it.tool_call_id ? `<span class="tag">${it.tool_call_id}</span>` : `<b>sin trazabilidad</b>`}</td><td>${fmt(it.cents)}</td></tr>`).join("");
  document.getElementById("out").innerHTML = `
    <div class="inv"><h3>Factura demo ${d.draft.number} — ${d.draft.customer}</h3>
    <table><tr><th>Concepto</th><th>Valor</th></tr>${items}
    <tr><td>Subtotal</td><td>${fmt(d.draft.subtotal_cents)}</td></tr>
    <tr><td>IVA 19%</td><td>${fmt(d.draft.iva_cents)}</td></tr>
    <tr><td><b>Total</b></td><td><b>${fmt(d.draft.total_cents)}</b></td></tr></table></div>
    <div class="${d.transmit ? "pass" : "block"}">
    <b>${d.transmit ? "TRANSMITIR: SI" : "TRANSMITIR: NO"}</b> — ${d.veredicto}</div>
    <pre class="mut">${JSON.stringify(d, null, 1)}</pre>`;
}
</script>
</body></html>
"""


def parse_money_cents(text: str) -> int:
    """Extrae la primera cifra de dinero y la devuelve en centavos (int, cero float)."""
    match = re.search(r"\$?\s*([\d][\d\.]*)", text.replace(",", "."))
    if not match:
        return 0
    return int(match.group(1).replace(".", "")) * 100


def parse_customer(text: str) -> str:
    """Cliente entre 'a' y 'por'; si no hay, valor por defecto honesto."""
    match = re.search(r"\bfactura\s+a\s+(.+?)\s+por\b", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().capitalize()
    return "Cliente demo"


def build_draft(text: str, with_tools: bool) -> dict:
    """Planner mock: interpreta la cifra como subtotal y suma IVA 19% (todo en centavos int)."""
    subtotal = parse_money_cents(text)
    iva = subtotal * IVA_RATE // 100
    item: dict = {"cents": subtotal, "concept": "servicios"}
    if with_tools:
        item["tool_call_id"] = "call_demo_1"
    draft = {
        "number": "DEMO-0001",
        "date": date.today().isoformat(),
        "customer": parse_customer(text),
        "items": [item],
        "subtotal_cents": subtotal,
        "iva_cents": iva,
        "total_cents": subtotal + iva,
        "amounts": [{"cents": subtotal, **({"tool_call_id": "call_demo_1"} if with_tools else {})}],
        "dian_schema_ok": True,
    }
    return draft


class Handler(BaseHTTPRequestHandler):
    server_version = "FiscalShield/1.1"

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, b'{"ok":true}')
        elif self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/verify":
            draft = self._json_body()
            if draft is None:
                self._send(400, b'{"transmit":false,"veredicto":"bloqueado: cuerpo invalido"}')
                return
            ok, msg = verify_draft(draft)
            self._send(200 if ok else 422, json.dumps({"transmit": ok, "veredicto": msg}).encode("utf-8"))
        elif self.path == "/api/draft":
            req = self._json_body()
            if req is None or not isinstance(req.get("text"), str):
                self._send(400, b'{"transmit":false,"veredicto":"bloqueado: texto requerido"}')
                return
            draft = build_draft(req["text"], bool(req.get("with_tools", True)))
            ok, msg = verify_draft(draft)
            payload = {
                "draft": {k: v for k, v in draft.items() if k != "amounts"},
                "transmit": ok,
                "veredicto": msg,
            }
            self._send(200, json.dumps(payload).encode("utf-8"))
        else:
            self._send(404, b'{"error":"not found"}')

    def log_message(self, *args: object) -> None:
        pass


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"fiscal-shield demo en puerto {port} (mock local)")
    server.serve_forever()


if __name__ == "__main__":
    main()
