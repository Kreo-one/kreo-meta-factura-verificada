# SDD — demo-evidence-suite (botón "Correr suite de verificación")

## Spec

Botón en `factura.kreo.lat` que ejecuta 20 casos deterministas en vivo contra los endpoints reales y muestra pass-rate + p95 medido en el navegador. Convierte el segmento de métricas del video en evidencia, no en diapositiva.

### Contratos inmutables

- `POST /api/verify` y `POST /api/extract`: sin cambios de firma ni semántica.
- Suite 100% cliente (JS): N=20 fijo, casos listados abajo, sin aleatoriedad.
- Todo importe en centavos `int`; cero `float`.
- Copy honesto: "schema del borrador", jamás "XML/XSD DIAN"; "planner degradado local" salvo key real.

### Matriz I/O

| ID | Entrada | Esperado | Test asociado |
|---|---|---|---|
| CASE-01..08 | 8 borradores válidos (montos 1, 1.000, 95.000, 2.450.000, 300.000, 10.000.000, 99, 500.000.000 cents, todos con `tool_call_id`) | `transmit:true`, HTTP 200 | suite[0..7] |
| CASE-09..14 | 6 borradores sin `tool_call_id` | `transmit:false`, `veredicto` contiene `tool_call_id` | suite[8..13] |
| CASE-15..17 | 3 borradores con `dian_schema_ok:false` | `transmit:false`, schema | suite[14..16] |
| CASE-18..19 | 2 borradores con `cents` no-int (`"2450000"`, `24.5`) | `transmit:false` | suite[17..18] |
| CASE-20 | `POST /api/extract` texto PYME estándar | 4 fields, cada uno con `tool_call_id` | suite[19] |
| CASE-FAIL | endpoint caído / no-JSON | fila marcada ERROR, suite no miente: cuenta como fallo | manejo en JS |

Done = 20/20 comportamientos esperados + p95 mostrado + KPIs del panel actualizados con valores de la suite.
