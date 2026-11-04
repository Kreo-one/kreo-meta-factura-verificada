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

## Pendientes
- Key `META_SPARK_API_KEY` + endpoint (pago COP$30.031) → ingest → envs Coolify → redeploy → el sello cambia a "Muse Spark (Meta, cloud)".
- Video 90 s + submit Cerebral Valley (deadline 4 nov 21:00 ET).
- Write-up del submission con KPIs medidos (opción 2 reservada para texto, no para el demo).
