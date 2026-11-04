# Prompt operativo — sesión de trabajo en kreo-meta-factura-verificada

Pega esto al abrir una sesión nueva para trabajar en este repo. El código vive
aquí; las herramientas pesadas viven en el skeleton y se invocan por ruta absoluta.

## 0. Dónde estoy y con qué trabajo

- Repo actual: `/home/lgc/proyectos/kreo-meta-factura-verificada` (origen: GitHub público `Kreo-one/kreo-meta-factura-verificada`, rama `main`).
- Skeleton (NO es este repo, solo provee herramientas): `/home/lgc/proyectos/kreo-one-skeleton`.
- Producción: `https://factura.kreo.lat` = app Coolify VPS-3 uuid `wduqj26h3ttu3ylpz6smnaiy` (construida desde `main` de GitHub). Duplicada de diagnóstico en VPS-1 uuid `alsx5hrwpcmnv3stjfb47mjq` (no tocar salvo orden expresa).
- Clave Meta: SOLO en vault/Coolify. Reglas: ingest-only, counts-only (longitudes, jamás valores), verify-before-use, fail-closed. Nunca `cat`, `echo` ni pegar valores en chat/logs.

## 1. Cómo invocar las herramientas del skeleton (ruta absoluta, sin cd)

```bash
S=/home/lgc/proyectos/kreo-one-skeleton
source $S/.agents/scripts/load-env.sh            # tokens del vault al entorno (counts-only)
bash $S/.agents/scripts/coolify-ctl.sh list      # inventario (lectura)
bash $S/.agents/scripts/coolify-ctl.sh env-verify app wduqj26h3ttu3ylpz6smnaiy META_SPARK_API_KEY
COOLIFY_ALLOW_MUTATION=1 bash $S/.agents/scripts/coolify-ctl.sh restart app <uuid>   # solo con orden expresa
# Deploy: coolify deploy uuid <uuid> (CLI directo, token vía load-env; jamás --api-token en argv)
# Ingesta de secretos: NUNCA pegar a mano en paneles; usar $S/.agents/scripts/ingest-tokens-from-file.sh
```

Comandos propios de este repo (corren aquí):

```bash
python3 -m py_compile src/server.py && python3 -m unittest discover -s tests   # 5/5 esperado
python3 scripts/post-deploy-check.py https://factura.kreo.lat --full           # cierre counts-only, exit 0 = verde
```

Git aquí es estándar (`add/commit/push` a `origin main`); NO usar `./guardar.sh` del skeleton (es de otro repo).

## 2. Estado actual (verificado 2026-11-04)

- Causa raíz del 401 resuelta: la key en Coolify tenía comillas literales (`len_raw=50` vs `len_sanitizada=48`); `sanitize_api_key()` en `src/server.py:179` lo corrige al consumir. Hipótesis UA y ASN/IP refutadas con sonda (las 3 variantes de UA dan 200).
- Producción: suite server-side 20/20, p95 ≈0.3–0.5s, sello `Muse Spark (Meta, cloud) · muse-spark-1.3 · api.meta.ai` con `tool_call_id` real. Relay temporal de diagnóstico ya retirado.
- Harness permanente portado al skeleton (rama `sdd/secret-env-harness`, commiteado y pusheado a Gitea): VO `SanitizedSecret`, `post-deploy-verify.sh`, skill `kreo-secret-harness`.
- Auditoría del dictamen externo cerrada en `openspec/changes/demo-evidence-suite/AUDITORIA-DICTAMEN.md`: no aplicar su snippet débil, no instalar WARP, quitar "Llama 3"/"Baseten" del submission (ya aplicado en `docs/SUBMISSION.md`).

## 3. Pendientes (lo único que falta es humano)

1. **Video 90s–3min**: wizard → factura → sabotaje bloqueado → suite en vivo → sello Muse Spark. Si el VPS fallara, la corrida local con key real es evidencia válida.
2. **Submit en Cerebral Valley** antes del 4 nov 21:00 ET, con el texto de `docs/SUBMISSION.md` (copiar-pegar, sin añadir Llama 3/Baseten/Workers/SHA-256).
3. Limpieza opcional: app duplicada VPS-1 `alsx...` (documentar o retirar cuando se decida).

## 4. Prohibiciones vigentes en este repo

- No afirmar integraciones sin evidencia (Llama 3, Baseten, Workers, SHA-256, XML/XSD DIAN, p95 no medido).
- No exponer secretos ni fragmentos (solo longitudes/conteos/códigos HTTP).
- No reintroducir el snippet débil del dictamen ni WARP.
- `src/agent.py` es mock local sin key: no "sanitizar" nada en él.
