# Premortem — demo-evidence-suite

## V-01: Fuga de la key Meta al repo público
- Escenario: al cablear el planner alguien pega `META_SPARK_API_KEY=...` en `server.py`/`.env` commiteado.
- Probabilidad: media. Impacto: crítico (revocación + exposición).
- Mitigación: key SOLO por entorno Coolify; T-2 incluye barrido de secretos pre-push; jamás `.env` en el repo (`.gitignore` lo excluye).

## V-02: Métricas como benchmark falso
- Escenario: p95 de 20 llamadas locales se presenta como SLA de producción.
- Probabilidad: alta (tentación de marketing). Impacto: pérdida de credibilidad ante jurado técnico.
- Mitigación: etiqueta visible "medido en tu navegador, N=20, casos deterministas listados en spec.md".

## V-03: Deploy rompe el healthcheck
- Escenario: cambio en PAGE rompe el servidor (sintaxis) y Coolify marca unhealthy.
- Probabilidad: baja. Impacto: demo caído antes del video.
- Mitigación: `py_compile` + smoke local antes de push; deploy con verificación inmediata y rollback = redeploy del commit anterior.

## V-04: Overclaim XML DIAN / Workers / SHA-256
- Escenario: copy del demo promete validación XSD, Edge o hashes que no existen.
- Probabilidad: media (presión del hackathon). Impacto: descalificación por falsedad.
- Mitigación: copy fijado en spec ("schema del borrador", "trazabilidad por tool_call_id"); revisión del texto en T-2.

## Resiliencia
- Sin key Meta: la suite corre igual (extractor local + gate real); el planner degradado es parte del diseño, no un fallo.
- Sin red: la página no funciona (demo en vivo por definición); el video grabado queda como respaldo.
