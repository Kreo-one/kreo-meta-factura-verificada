# Spec: dictamen-fixes — aplicar puntos válidos de AUDITORIA-DICTAMEN.md

## Problema
`AUDITORIA-DICTAMEN.md` (secciones 3, 4, 5) encontró claims sin evidencia o
desactualizados en el material del submission: "Llama 3" y "Fallback Baseten"
no tienen código ni sonda que los respalde; KPI-3 dice "mock local" cuando la
API real ya está viva y medida; el subtítulo de la página y el log de arranque
dicen "mock local" aunque el planner usa Muse Spark con key presente.

## Alcance (solo texto/docs + 2 strings de UI; cero lógica)
1. `README.md`: quitar "Fallback Baseten medible"; KPI-3 con p95 medido.
2. `src/server.py`: subtítulo de la página y mensaje de arranque reflejan el
   planner real (Muse Spark con key, mock sin key). Sin cambios de lógica.
3. `docs/SUBMISSION.md` nuevo: texto corregido del formulario (sin Llama 3,
   DIAN matizado, p95 medido) listo para copiar-pegar.
4. `src/agent.py`: verificado sin uso de la key (mock local + print
   informativo) → sin cambios; se documenta como N/A.

## Fuera de alcance
Snippet de sanitización del dictamen (más débil que `sanitize_api_key`
desplegado), User-Agent como "fix", WARP/ASN, puntaje 8.8/10. Todo refutado
en `AUDITORIA-DICTAMEN.md`; no se toca.

## Matriz I/O
| ID | Entrada | Salida esperada |
|---|---|---|
| CASE-01 | `grep -rin "baseten\|llama 3\|Llama 3" README.md docs/ src/ --include=*.py` (excluyendo AUDITORIA y este plan) | 0 hits |
| CASE-02 | `grep -n "mock local" README.md src/server.py` | 0 hits en descripciones de comportamiento (el mock sigue existiendo como fallback documentado en SUBMISSION.md) |
| CASE-03 | `python3 -m py_compile src/server.py` + `unittest discover -s tests` | OK + 5/5 |
| CASE-04 | `post-deploy-check.py <prod>` (solo lectura) | OK (el cambio es docs/UI; confirma que nada se rompió) |

## Done
CASE-01..04 en verde + commit + push a `main` público.
