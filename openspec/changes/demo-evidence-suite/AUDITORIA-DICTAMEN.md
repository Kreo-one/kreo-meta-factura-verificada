# Auditoría del dictamen externo — veredicto por sección (2026-11-04)

Metodología: cada afirmación del dictamen se contrasta contra evidencia medida
de esta sesión (sondas reales, código en `main`, producción viva). Cero
especulación: lo no medido se marca como tal.

## Veredicto global: APROBADO CON CORRECCIONES (6 rechazos parciales)

La tesis ("la IA propone, el sistema prueba"), el video y el formulario son
sólidos. Los tres "fixes" técnicos del dictamen están obsoletos o refutados:
aplicarlos hoy sería una regresión o un riesgo innecesario.

## Sección 1 — Puntaje 8.8/10: RECHAZADO (precisión fabricada)

No existe rúbrica citada ni medición que sostenga el "8.8". Un jurado técnico
detecta puntajes auto-asignados como humo. Reemplazar por hechos medidos:
suite 20/20 en producción, p95 291–477 ms, `tool_call_id` real de
`muse-spark-1.3` visible en la demo viva.

## Sección 2A — Sanitización de la key: YA APLICADO Y SUPERIOR (no tocar)

El snippet propuesto (`raw_key.strip().strip("'").strip('"')`) es más débil
que lo desplegado en `src/server.py:179` (`sanitize_api_key`: quita además
`\r`/`\n` y espacios externos). Causa raíz medida: `len_raw=50` vs
`len_sanitizada=48`, 2 caracteres removidos por comillas, 0 por espacios.
Pegar el snippet del dictamen sobre el código actual sería una regresión
(perdería el manejo de CR/LF). `src/agent.py` no usa la key (solo mock local
+ `META_MODEL_API_KEY` informativa): el checklist que pide sanitizar
"server.py y agent.py" es correcto solo para `server.py`.

## Sección 2B — User-Agent como causa del 401: REFUTADO

Medido dentro del contenedor con la clave ya sanitizada: `GET /v1/models`
→ 200 con las TRES variantes (`KreOFiscalShield/1.0`, `Mozilla/5.0` y
`Python-urllib` por defecto). El UA por defecto NO es bloqueado por
`api.meta.ai`. El header explícito ya presente en `server.py:220` se conserva
como robustez, pero el informe y el video NO deben presentarlo como el fix:
el fix fue la sanitización (Sección 2A).

## Sección 2C — Bloqueo por ASN / Cloudflare WARP: REFUTADO, NO APLICAR

Con la clave sanitizada el egreso directo desde los contenedores OVH devuelve
200 (sonda real + suite 20/20 en producción). No hay filtro por ASN. Instalar
WARP en el host VPS (infraestructura compartida) para "solucionar" un problema
inexistente introduciría riesgo de enrutamiento sin beneficio. El relay
temporal usado en el diagnóstico ya fue retirado.

## Sección 3 — "Muse Spark 1.3 / Llama 3": CORREGIR (quitar Llama 3)

Lo verificado en producción es exclusivamente `muse-spark-1.3` con
`tool_call_id` real (`call_fa866e66-...`). La vía Llama de Workers AI dio 401
en esta sesión y no está integrada. Nombrar "Llama 3" en el formulario es un
claim sin evidencia: usar solo "Muse Spark 1.3".

## Sección 4 — "Validación esquema DIAN": MATIZAR

`src/verify.py` aplica reglas estructurales deterministas (enteros en
centavos, presencia de `tool_call_id`, flags de schema), no el XSD oficial de
la DIAN. Decir "esquema DIAN" sin calificativo invita a una pregunta del
jurado que no se puede sostener. Formulación honesta: "validación estructural
compatible con las reglas numéricas DIAN (enteros, sin flotantes)".

## Sección 5 — README: dos deudas propias detectadas en esta auditoría

1. "Fallback Baseten medible": Baseten no aparece en ningún código, config o
   sonda de esta sesión. Quitar o evidenciar antes del submit.
2. KPI-3 desactualizado: dice "(mock local; con API real + fallback Baseten)"
   pero la API real ya está viva y medida (p95 291–477 ms). Actualizar al
   valor medido.

## Sección 6 — Video y formulario: APROBADOS con ajustes menores

- El segmento 1:30–2:15 ya es evidencia ejecutable (botón de suite en la
  página + `scripts/post-deploy-check.py --full`), no diapositiva. Usar el p95
  medido, no el genérico "<3s".
- El texto de formulario propuesto es correcto (scope Python vs ERP host,
  fallback honesto, sin versiones infladas). Aplicar las correcciones de las
  secciones 3 y 4.
- Checklist: el repo ya es público; `post-deploy-check.py` existe y cierra en
  verde contra producción. Solo falta el video y el submit humano.
