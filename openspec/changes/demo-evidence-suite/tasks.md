# Tasks — demo-evidence-suite

#### [T-1] Botón suite + 20 casos JS + panel de resultados
- **Modo:** `[S]`
- **Test primero:** `python3 -c` smoke de los 20 payloads contra `/api/verify` y `/api/extract` en local (script efímero, no se commitea)
- **Archivo Fuente:** `src/server.py` (constante PAGE: botón + `runSuite()` + tabla)
- **Verificación:** `curl` local a `/` 200 + ejecución manual de la suite en navegador/local
- **Done Checkpoint:** 20/20 esperado, p95 visible, KPIs actualizados
- [x] Completado

#### [T-2] Auditoría equivalente (el auditor PHP no aplica a este repo)
- **Modo:** `[S]`
- **Verificación:** `python3 -m py_compile src/*.py`; `grep -rniE "BEGIN .*PRIVATE KEY|ghp_|gho_|sk-ant|META_SPARK_API_KEY\s*=\s*['\"][^'\"]" src/ README.md docs/` → 0 hits (sin secretos); `git status` limpio de `.env`
- **Done Checkpoint:** 0 secretos, sintaxis OK
- [x] Completado

#### [T-3] Deploy + verificación en vivo + evidencias de cierre
- **Modo:** `[S]`
- **Verificación:** `coolify deploy uuid …` → `finished`; `curl https://factura.kreo.lat/` 200; suite ejecutada contra prod vía endpoint (smoke server-side de los 20 casos)
- **Archivos:** `VOICE_EVIDENCE.md` + `CLOSING_REPORT.md` en el change
- **Done Checkpoint:** prod en el commit nuevo, 20/20 verificado en vivo
- [x] Completado
