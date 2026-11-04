# Premortem: dictamen-fixes

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| V-01 | Un "Llama 3"/"Baseten" sobrevive en algún archivo fuera del grep | Baja | Alta (claim sin evidencia ante el jurado) | CASE-01 grep insensible a mayúsculas sobre README/docs/src |
| V-02 | Cambiar strings de UI rompe la página o los tests | Baja | Media | Sin cambios de lógica; CASE-03 py_compile + unittest |
| V-03 | El redeploy no toma los strings y el jurado ve texto viejo | Baja | Media | El deploy Coolify reconstruye desde `main`; CASE-04 verifica prod tras el push |
