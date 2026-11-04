#!/usr/bin/env python3
"""Check counts-only de cierre de deploy — KreO Fiscal Shield.

Uso:
    python3 scripts/post-deploy-check.py [base_url] [--full]

Sin --full corre 4 sondas (health, verify valido, verify bloqueado, extract
con sello Muse Spark real). Con --full corre ademas la suite determinista
de 20 casos contra la URL. Fail-closed: cualquier FAIL -> exit 1.

Counts-only (doctrina kreo-token-ops): si META_SPARK_API_KEY esta en el
entorno local solo se reportan longitudes y si la sanitizacion cambia el
valor; jamas el valor, hashes ni fragmentos.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

USER_AGENT = "KreOFiscalShield/1.0 (Linux; x86_64) Mozilla/5.0"


def sanitize_api_key(raw: str) -> str:
    return raw.replace("\r", "").replace("\n", "").strip().strip('"').strip("'").strip()


def call(base: str, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        base + path,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as http_error:
        try:
            return http_error.code, json.loads(http_error.read().decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return http_error.code, {}
    except Exception as error:  # noqa: BLE001 - el check reporta y sale fail-closed
        return 0, {"error": type(error).__name__}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    base = (args[0] if args else "https://factura.kreo.lat").rstrip("/")
    full = "--full" in sys.argv
    failures = 0

    def report(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        failures += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'} {name} {detail}".rstrip())

    raw_key = os.getenv("META_SPARK_API_KEY", "")
    if raw_key:
        print(
            f"INFO env META_SPARK_API_KEY len_raw={len(raw_key)} "
            f"len_sanitizada={len(sanitize_api_key(raw_key))} "
            f"sanitizacion_cambia={sanitize_api_key(raw_key) != raw_key}"
        )

    status, body = call(base, "GET", "/health")
    report("health", status == 200 and body.get("ok") is True, f"http={status}")

    status, body = call(base, "POST", "/api/verify", {"amounts": [{"cents": 1000, "tool_call_id": "t"}], "dian_schema_ok": True})
    report("verify-valido-transmite", status == 200 and body.get("transmit") is True, f"http={status}")

    status, body = call(base, "POST", "/api/verify", {"amounts": [{"cents": 1000}], "dian_schema_ok": True})
    report("verify-sin-tool-bloquea", status == 422 and body.get("transmit") is False, f"http={status}")

    status, body = call(
        base, "POST", "/api/extract",
        {"text": "Mi empresa es Comercial Andina SAS, emitimos 120 facturas al mes"},
    )
    source = str(body.get("source", ""))
    report(
        "extract-sello-muse-spark",
        status == 200 and "Muse Spark (Meta, cloud)" in source and bool(body.get("tool_call_id")),
        f"http={status} degradado={'degradado' in source}",
    )

    if full:
        jobs: list[tuple[dict, bool]] = []
        for cents in (1, 1000, 9500000, 245000000, 30000000, 1000000000, 99, 50000000000):
            jobs.append(({"amounts": [{"cents": cents, "tool_call_id": "t"}], "dian_schema_ok": True}, True))
        for cents in (1, 1000, 9500000, 245000000, 30000000, 10000000):
            jobs.append(({"amounts": [{"cents": cents}], "dian_schema_ok": True}, False))
        for _ in range(3):
            jobs.append(({"amounts": [{"cents": 1000, "tool_call_id": "t"}], "dian_schema_ok": False}, False))
        jobs.append(({"amounts": [{"cents": "2450000", "tool_call_id": "t"}], "dian_schema_ok": True}, False))
        jobs.append(({"amounts": [{"cents": 24.5, "tool_call_id": "t"}], "dian_schema_ok": True}, False))

        passed = 0
        latencies: list[float] = []
        for payload, expect in jobs:
            started = time.time()
            status, body = call(base, "POST", "/api/verify", payload)
            latencies.append((time.time() - started) * 1000)
            passed += (status == 200 and body.get("transmit") is True) if expect else (status == 422 and body.get("transmit") is False)
        started = time.time()
        status, body = call(base, "POST", "/api/extract", {"text": "Mi empresa es Café Andino LTDA, con 60 facturas"})
        latencies.append((time.time() - started) * 1000)
        fields = body.get("fields") or []
        passed += status == 200 and len(fields) == 2 and all(f.get("tool_call_id") for f in fields)
        latencies.sort()
        p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)]
        report("suite-20-casos", passed == 20, f"{passed}/20 p95={p95:.0f}ms")

    print(f"RESULTADO: {'OK' if failures == 0 else 'FAIL'} checks_fallidos={failures} base={base}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
