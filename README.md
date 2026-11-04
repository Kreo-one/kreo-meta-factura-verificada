# Kreo.One — ERP SaaS agéntico (módulo verificable: Kreo Fiscal Shield)

Este repo público es el **módulo verificable y desplegable del ERP SaaS agéntico Kreo.One**: un wizard conversacional (Muse Spark) que propone, herramientas deterministas que calculan, y un verifier que decide antes de transmitir. El core del ERP (`kreo-one-skeleton`, GitHub PRIVATE) no se expone aquí; esto es su prueba pública viva.

## Qué demuestra
Voz/texto → borrador factura → gate determinista que bloquea todo número sin `tool_call_id` → validación esquema DIAN → `transmit` solo si el verifier pasa.

## Arquitectura
`Muse Spark 1.3 (planner, OpenAI-compatible, tool-calling) → tools deterministas → verifier → transmit solo con veredicto PASS`. Sin key, mock local honesto (etiquetado en pantalla). Cero-float: centavos `int`, nada de `float` para dinero.

## Correr local
```
pip install -r requirements.txt
python src/verify.py
python src/agent.py "factura a cliente X por 2450000 + IVA"
PORT=8080 python src/server.py  # web demo: / (pagina), /health, POST /api/verify
```

## Deploy (Coolify, VPS-3)
`Dockerfile` stdlib-only. App publica desde este repo, build-pack `dockerfile`,
puerto 8080, health-check `/health`, dominio `https://factura.kreo.lat`.

## Tests y cierre de deploy
```
python3 -m unittest discover -s tests   # regresion 401: clave con comillas envolventes igual autentica
python3 scripts/post-deploy-check.py https://factura.kreo.lat --full   # cierre counts-only, fail-closed (exit 1 si algo falla)
```
`post-deploy-check.py` verifica health, transmit/bloqueo del verificador y que
el extract lleve el sello real de Muse Spark (sin sello = deploy no cerrado).
Si `META_SPARK_API_KEY` esta en su entorno solo reporta longitudes, jamas el valor.

## Trazabilidad
Cada cifra del borrador referencia `tool_call_id`. Sin `tool_call_id` no hay transmit. Ver `src/verify.py`.

## KPIs (SaaS-S, verificables)
- KPI-1: 100% cifras con `tool_call_id` (0 escritas por el modelo).
- KPI-2: 100% schema DIAN pass antes de transmitir.
- KPI-3: p95 ≈0.3–0.5s texto a borrador, medido en producción (suite server-side 20/20 vía `scripts/post-deploy-check.py --full`).

## Licencia
MIT — solo este slice. El core kreo.one sigue privado.
