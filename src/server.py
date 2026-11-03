"""Demo web Kreo Fiscal Shield: planner mock + gate determinista real.

Solo stdlib. Endpoints:
  GET  /         pagina demo (flujo: texto -> borrador -> veredicto)
  GET  /health   chequeo Coolify
  POST /api/verify  {"amounts":[...],"dian_schema_ok":bool} -> veredicto (contrato estable)
  POST /api/draft   {"text":str,"with_tools":bool} -> borrador + veredicto
  POST /api/extract {"text":str} -> campos del negocio con tool_call_id + ahorro estimado
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
body{font-family:system-ui,sans-serif;max-width:1080px;margin:1.5rem auto;padding:0 1rem;color:#1a1a1a}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media (max-width:820px){.grid{grid-template-columns:1fr}}
.card{border:1px solid #ddd;border-radius:10px;padding:1rem}
.msg{margin:.5rem 0;padding:.6rem .8rem;border-radius:8px;max-width:92%}
.ai{background:#eef3ff}.me{background:#f2f2f2;text-align:left;margin-left:auto}
textarea{width:100%;height:3rem;font-size:1rem;padding:.5rem;box-sizing:border-box}
button{padding:.55rem 1rem;margin:.3rem .2rem;font-size:.95rem;cursor:pointer}
.chip{display:inline-block;background:#eee;border-radius:10px;padding:.15rem .55rem;margin:.15rem;font-size:.82rem;font-family:monospace}
.chip.ok{background:#d9f2d9}.chip.bad{background:#f8d7d7}
.inv table{width:100%;border-collapse:collapse}
.inv td,.inv th{border-bottom:1px solid #eee;padding:.35rem;text-align:right}
.inv td:first-child,.inv th:first-child{text-align:left}
.pass{background:#e6f7e6;border:1px solid #2c7a2c;padding:.7rem;border-radius:6px;margin-top:.7rem}
.block{background:#fde8e8;border:1px solid #a33;padding:.7rem;border-radius:6px;margin-top:.7rem}
.mut{font-size:.82rem;color:#666}
.kpi{display:flex;gap:.6rem;flex-wrap:wrap}.kpi div{background:#f7f7f7;border:1px solid #e3e3e3;border-radius:8px;padding:.45rem .7rem;font-size:.85rem}
</style>
</head><body>
<h1>Kreo Fiscal Shield — el agente propone, el verificador decide</h1>
<p class="mut">Wizard del ERP SaaS agentico Kreo.One (planner mock local; con la key de Meta usa Muse Spark — el gate no cambia).
Cada cifra lleva su <code>tool_call_id</code>: sin trazabilidad, no hay transmit.</p>
<div class="grid">
 <div class="card">
  <div id="chat"></div>
  <textarea id="t" placeholder="Cuéntanos de tu empresa…">Mi empresa es Distribuciones Bolivar SAS, facturamos 95 facturas al mes, gasto 40 horas contables y pago 300.000 en software</textarea><br>
  <button onclick="send()" id="sendBtn">Enviar</button>
  <button onclick="sabotage()" title="El LLM escribe la cifra sin tool_call_id">Simular LLM sin herramientas</button>
  <p class="mut">Paso 1: cuéntanos tu operación. Paso 2: escribe tu primera factura tras el análisis.</p>
 </div>
 <div>
  <div class="card"><h3>Datos extraídos (con trazabilidad)</h3><div id="chips"><span class="mut">Sin datos aún…</span></div>
  <div id="roi"></div></div>
  <div class="card inv" style="margin-top:1rem"><h3>Factura en vivo</h3><div id="inv"><span class="mut">Tu primera factura aparece aquí…</span></div><div id="verdict"></div>
  <div class="kpi" style="margin-top:.7rem">
    <div>Grounding: <b id="kGround">—</b></div>
    <div>Schema DIAN: <b id="kSchema">—</b></div>
    <div>p95 sesión: <b id="kP95">—</b></div>
  </div></div>
 </div>
</div>
<script>
const fmt = c => "$ " + (c/100).toLocaleString("es-CO");
const lat = []; let step = 0, sabotaged = false;
function bubble(txt, cls){
  const d = document.createElement("div"); d.className = "msg " + cls; d.innerHTML = txt;
  document.getElementById("chat").appendChild(d); d.scrollIntoView({behavior:"smooth"});
}
async function timed(path, payload){
  const t0 = performance.now();
  const r = await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  lat.push(performance.now() - t0);
  lat.sort((a,b)=>a-b);
  document.getElementById("kP95").textContent = Math.round(lat[Math.ceil(0.95*lat.length)-1]) + " ms";
  return r.json();
}
bubble("¡Bienvenido a KreO.One! Soy Sofía. Cuéntame de tu empresa: cuántas facturas emites, cuánto tiempo gastas en contabilidad y cuánto pagas en software.","ai");
async function send(){
  const el = document.getElementById("t"); const text = el.value.trim(); if(!text) return;
  bubble(text,"me");
  if(step === 0){
    const d = await timed("/api/extract",{text});
    const f = d.fields;
    document.getElementById("chips").innerHTML = f.map(x =>
      `<span class="chip ok">${x.field}: ${x.display} · ${x.tool_call_id}</span>`).join("");
    document.getElementById("kGround").textContent = "100% (" + f.length + "/" + f.length + ")";
    document.getElementById("kSchema").textContent = "pendiente factura";
    document.getElementById("roi").innerHTML = `<p><b>Ahorro estimado/mes:</b> ${fmt(d.savings_cents)} (estimación demo: −35% software + 70% de tu tiempo contable).</p>`;
    bubble(`Perfecto. Detecté ${f.length} datos con trazabilidad total. Tu ahorro estimado es <b>${fmt(d.savings_cents)}/mes</b>. Ahora escribe tu primera factura, p. ej.: <i>factura a Distribuciones Bolivar por 2.450.000 + IVA</i>.`,"ai");
    el.value = "factura a Distribuciones Bolivar por 2.450.000 + IVA por servicios contables"; step = 1; document.getElementById("sendBtn").textContent = "Generar factura";
  } else {
    const d = await timed("/api/draft",{text, with_tools: !sabotaged, fields_count: 0});
    renderInvoice(d);
    bubble(d.transmit ? "Factura validada por el verificador: schema DIAN OK y cada cifra con <code>tool_call_id</code>. Lista para transmitir."
                       : "El verificador bloqueó la factura: hay cifras sin <code>tool_call_id</code>. El agente propone; el verificador decide.","ai");
    sabotaged = false;
  }
}
function sabotage(){ sabotaged = true; bubble("Modo sabotaje: el LLM escribirá la próxima cifra sin herramientas.","ai"); }
function renderInvoice(d){
  const items = d.draft.items.map(it =>
    `<tr><td>${it.concept} ${it.tool_call_id ? `<span class="chip ok">${it.tool_call_id}</span>` : `<span class="chip bad">sin trazabilidad</span>`}</td><td>${fmt(it.cents)}</td></tr>`).join("");
  document.getElementById("inv").innerHTML = `
    <h4 style="margin:.2rem 0">Factura demo ${d.draft.number} — ${d.draft.customer} (${d.draft.date})</h4>
    <table><tr><th>Concepto</th><th>Valor</th></tr>${items}
    <tr><td>Subtotal</td><td>${fmt(d.draft.subtotal_cents)}</td></tr>
    <tr><td>IVA 19%</td><td>${fmt(d.draft.iva_cents)}</td></tr>
    <tr><td><b>Total</b></td><td><b>${fmt(d.draft.total_cents)}</b></td></tr></table>`;
  document.getElementById("verdict").innerHTML = `<div class="${d.transmit ? "pass" : "block"}"><b>${d.transmit ? "TRANSMITIR: SI" : "TRANSMITIR: NO"}</b> — ${d.veredicto}</div>`;
  document.getElementById("kSchema").textContent = d.draft.dian_schema_ok ? "OK" : "FALLA";
  document.getElementById("kGround").textContent = d.transmit ? "100%" : "cifras sin fuente";
}
</script>
</body></html>
"""

HOUR_VALUE_CENTS = 2_500_000


def extract_business(text: str) -> dict:
    """Extractor determinista (misma heurística del fallback del ERP) con trazabilidad por campo."""
    fields: list[dict] = []

    def add(field: str, value, cents: int | None = None) -> None:
        display = fmt_pesos(cents) if cents is not None else str(value)
        fields.append({"field": field, "value": value, "display": display, "tool_call_id": "call_extract_1"})

    match = re.search(
        r"(?:empresa(?: es)?|negocio(?: es)?|somos)\s+([A-Za-z0-9\u00c0-\u00ff\s]+?(?:SAS|S\.A\.S\.|LTDA|Ltda|S\.A\.|E\.U\.|Real))",
        text, re.IGNORECASE)
    if match:
        add("company_name", match.group(1).strip())
    match = re.search(r"(\d+)\s*(?:facturas|comprobantes|factura)", text, re.IGNORECASE)
    if match:
        add("monthly_invoices", int(match.group(1)))
    match = re.search(r"(\d+)\s*(?:horas|hora|hrs)", text, re.IGNORECASE)
    hours = int(match.group(1)) if match else 0
    if match:
        add("accounting_hours", hours)
    match = re.search(r"(?:pago|pagamos|software(?: de)?)\s*(?:\$)?\s*([\d\.]+)", text, re.IGNORECASE)
    software_cents = int(match.group(1).replace(".", "")) * 100 if match else 0
    if match:
        add("current_software_cost_cents", software_cents, software_cents)

    savings = software_cents * 35 // 100 + hours * 70 * HOUR_VALUE_CENTS // 100
    return {"fields": fields, "savings_cents": savings}


def fmt_pesos(cents: int) -> str:
    return f"$ {cents // 100:,}".replace(",", ".")


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
        if self.path == "/api/extract":
            req = self._json_body()
            if req is None or not isinstance(req.get("text"), str):
                self._send(400, b'{"error":"texto requerido"}')
                return
            result = extract_business(req["text"])
            self._send(200, json.dumps(result).encode("utf-8"))
        elif self.path == "/api/verify":
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
