"""Kreo Fiscal Shield web demo: mock planner + real deterministic gate.

Stdlib only. Endpoints:
  GET  /,/app   audited frontend 7/7 (same origin as /api/...)
  GET  /health   Coolify check
  POST /api/verify  {"amounts":[...],"dian_schema_ok":bool} -> verdict (stable contract)
  POST /api/draft   {"text":str,"with_tools":bool} -> draft + verdict
  POST /api/extract {"text":str} -> business fields with tool_call_id + estimated savings
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from verify import verify_draft

IVA_RATE = 19

APP_PATH = Path(__file__).resolve().parent / "static" / "app.html"

HOUR_VALUE_CENTS = 2_500_000


EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_business_fields",
        "description": "Extrae datos del negocio desde lenguaje natural",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {"type": ["string", "null"]},
                "monthly_invoices": {"type": ["integer", "null"]},
                "accounting_hours": {"type": ["integer", "null"]},
                "current_software_cost_cents": {"type": ["integer", "null"]},
            },
        },
    },
}


def sanitize_api_key(raw: str) -> str:
    """Clave lista para el header Authorization.

    Coolify/Docker pueden guardar el valor con comillas literales envolventes
    o con CR/LF; un header con esos bytes es rechazado con 401 (regresion
    fijada en tests/test_planner_auth.py).
    """
    return raw.replace("\r", "").replace("\n", "").strip().strip('"').strip("'").strip()


def meta_planner_fields(text: str) -> dict | None:
    """Planner Muse Spark (Meta, cloud): tool-calling real con trazabilidad de la llamada.

    Contrato idéntico al del ERP (config/neuron.php meta_spark): endpoint y key
    por entorno, modelo muse-spark-1.3. Devuelve None si no hay credenciales o si
    la llamada falla (auth/timeout) — el caller degrada al extractor local.
    """
    endpoint = os.getenv("META_SPARK_PLANNER_ENDPOINT", "").strip()
    api_key = sanitize_api_key(os.getenv("META_SPARK_API_KEY", ""))
    model = os.getenv("META_SPARK_PLANNER_MODEL", "muse-spark-1.3").strip()
    if not endpoint or not api_key:
        return None

    import urllib.error
    import urllib.request

    payload = {
        "model": model,
        "reasoning_effort": "low",
        "messages": [
            {"role": "system", "content": "Extrae los datos del negocio con la herramienta. Nada de texto libre."},
            {"role": "user", "content": text},
        ],
        "tools": [EXTRACT_TOOL],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "KreOFiscalShield/1.0 (Linux; x86_64) Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        print(f"[planner] meta http={http_error.code}", flush=True)
        return None
    except Exception as error:  # noqa: BLE001 - honest degradation on any failure
        print(f"[planner] meta fallo={type(error).__name__}", flush=True)
        return None

    choices = body.get("choices") or []
    if not choices:
        return None
    tool_calls = (choices[0].get("message") or {}).get("tool_calls") or []
    if not tool_calls:
        return None

    call = tool_calls[0]
    try:
        args = json.loads((call.get("function") or {}).get("arguments") or "{}")
    except json.JSONDecodeError:
        return None

    fields: list[dict] = []
    software_cents = args.get("current_software_cost_cents") or 0
    for name in ("company_name", "monthly_invoices", "accounting_hours", "current_software_cost_cents"):
        value = args.get(name)
        if value is None:
            continue
        display = fmt_pesos(value) if name == "current_software_cost_cents" and isinstance(value, int) else str(value)
        fields.append({"field": name, "value": value, "display": display, "tool_call_id": call.get("id", "call_meta")})

    hours = args.get("accounting_hours") or 0
    savings = (software_cents * 35 // 100 if isinstance(software_cents, int) else 0) + hours * 70 * HOUR_VALUE_CENTS // 100
    host = endpoint.split("/")[2] if "://" in endpoint else endpoint
    return {
        "fields": fields,
        "savings_cents": savings,
        "source": f"Muse Spark (Meta, cloud) · {model} · {host}",
        "tool_call_id": call.get("id", "call_meta"),
    }


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
    return {"fields": fields, "savings_cents": savings, "source": "degradado local (sin key Meta)"}


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
        elif self.path in ("/", "/index.html", "/app"):
            try:
                body = APP_PATH.read_bytes()
            except OSError:
                self._send(404, b'{"error":"not found"}')
            else:
                self._send(200, body, "text/html; charset=utf-8")
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/extract":
            req = self._json_body()
            if req is None or not isinstance(req.get("text"), str):
                self._send(400, b'{"error":"texto requerido"}')
                return
            result = meta_planner_fields(req["text"]) or extract_business(req["text"])
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
    print(f"fiscal-shield demo en puerto {port} (Muse Spark con key, mock sin key)")
    server.serve_forever()


if __name__ == "__main__":
    main()
