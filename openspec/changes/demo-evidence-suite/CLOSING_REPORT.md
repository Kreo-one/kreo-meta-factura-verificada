# CLOSING_REPORT — demo-evidence-suite

## Informe técnico
- Botón "Correr suite de verificación (20 casos)" en `src/server.py` (PAGE): ejecuta 8 válidos + 6 sin tool + 3 schema roto + 2 tipos inválidos + 1 extract, todo contra endpoints reales, con tabla de resultados y p95 medido en navegador.
- `POST /api/verify` y `POST /api/extract` sin cambios de firma.
- Smoke previo (script efímero, no commiteado): 20/20 local, p95 2.5 ms.
- Auditoría equivalente: `py_compile` OK, barrido de secretos 0 hits, `.gitignore` excluye `.env`.
- Deploy Coolify `ds98jttuvznp8ylysndy3r6z` → `finished` (commit `b0b0952`).
- Verificación en vivo: página 200 + botón presente; 19/19 verify + extract 2/2 trazados vía curl (con UA; ver nota).
- Nota operativa: Cloudflare desafía el UA por defecto de `Python-urllib` (respuestas vacías). El `fetch` del navegador funciona. Quien scriptee contra la API debe poner `User-Agent` propio. No es defecto del demo.

## Informe no técnico (negocio)
El demo ahora cuenta la historia completa en 90 segundos: Sofía conversa, extrae datos con trazabilidad visible, estima el ahorro, genera la primera factura y —si el modelo intenta escribir una cifra sin herramientas— el verificador la bloquea en pantalla. El botón de suite convierte el segmento de métricas del video en evidencia ejecutada en vivo (20/20 + p95 real), no en diapositiva. La key Meta real sigue pendiente: sin ella el planner corre degradado honesto, y la página lo dice.

## Resolución 401 Meta (2026-11-04)
- Causa raíz: el valor de `META_SPARK_API_KEY` en Coolify quedó guardado con comillas literales envolventes. El header enviado era `Authorization: Bearer "<key>"` y Meta respondía `401 invalid_api_key` solo desde los contenedores; la misma clave sin comillas responde 200 desde cualquier origen.
- Evidencia (counts-only): `len_raw=50`, `len_sanitizada=48`, caracteres removidos por strip de espacios = 0, por strip de comillas = 2. Con la clave sanitizada: `GET /v1/models` 200 y `POST /v1/chat/completions` 200 con `tool_calls` y `tool_call_id` real, desde dentro del contenedor.
- Hipótesis descartadas con prueba: User-Agent (defecto también da 200 tras sanitizar), ASN/IP OVH y WARP/túnel (innecesarios: el egreso directo funciona), caracteres `\r`/`\n` (ausentes). `tool_choice` forzado NO se usa: la API solo soporta `"auto"` (400 verificado); `reasoning_effort: "low"` sí es aceptado y quedó fijo en el payload.
- Fix en `src/server.py` (commit `4b969f0`): sanitización estricta de la clave (sin `\r`/`\n`, sin comillas envolventes), `User-Agent` explícito y modelo por defecto `muse-spark-1.3`.
- Verificación en producción (`https://factura.kreo.lat`): suite server-side 20/20 PASS, p95 477 ms, y el caso extract reporta `Muse Spark (Meta, cloud) · muse-spark-1.3 · api.meta.ai` con `tool_call_id` real. El relay temporal de egreso usado durante el diagnóstico fue retirado.

## Pendientes
- Video 90 s + submit Cerebral Valley (deadline 4 nov 21:00 ET).
- Write-up del submission con KPIs medidos (opción 2 reservada para texto, no para el demo).
