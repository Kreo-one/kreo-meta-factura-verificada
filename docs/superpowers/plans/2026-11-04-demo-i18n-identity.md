# Demo i18n + identidad — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** La página demo sirve ES/EN con autodetección y toggle, y tiene identidad propia (logo SVG + favicon), sin salir de stdlib ni tocar endpoints.

**Architecture:** Todo el cambio vive en el string `PAGE` de `src/server.py`: diccionario `I18N` ES/EN en el JS inline, `setLang()` que aplica `data-i18n`/`data-i18n-ph`/`data-i18n-title`, idioma inicial desde `localStorage` o `navigator.language`, y marca escudo SVG inline + favicon data-URI. Sin archivos nuevos salvo el test.

**Tech Stack:** Python stdlib (`http.server`), JS vanilla inline, `unittest`.

**Spec:** diseño aprobado en chat (todo junto, auto+botón, SVG inline, solo `src/server.py`).

## Global Constraints

- Solo stdlib; cero dependencias y cero archivos de assets nuevos.
- Ningún endpoint (`/`, `/health`, `/api/verify`, `/api/draft`, `/api/extract`) cambia de contrato.
- `post-deploy-check.py --full` debe seguir en verde.
- No exponer secretos; conteos/longitudes como máximo.

---

### Task 1: Test rojo del chrome localizado

**Files:**
- Create: `tests/test_page_chrome.py`
- Test: `python3 -m unittest tests.test_page_chrome -v`

**Interfaces:**
- Consumes: `server.PAGE` (string, ya existe en `src/server.py:22`).
- Produces: `LocalizedChromeTest.test_page_ships_i18n_toggle_and_identity`.

- [ ] **Step 1: Write the failing test**

```python
class LocalizedChromeTest(unittest.TestCase):
    def test_page_ships_i18n_toggle_and_identity(self) -> None:
        page = server.PAGE
        self.assertIn('id="langBtn"', page)
        self.assertIn("navigator.language", page)
        self.assertIn("localStorage", page)
        self.assertIn('"es"', page)
        self.assertIn('"en"', page)
        self.assertIn("Fiscal Shield", page)
        self.assertIn('rel="icon"', page)
        self.assertIn("<svg", page)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_page_chrome -v`
Expected: FAIL with `'id="langBtn"' not found`.

### Task 2: Chrome estático (favicon, marca, data-i18n)

**Files:**
- Modify: `src/server.py` (head + header + tarjetas, `data-i18n*` sin tocar lógica).

- [ ] **Step 1: favicon data-URI en `<head>`** (escudo verde + check, SVG URL-encoded).
- [ ] **Step 2: header `.brand`** con SVG inline, `h1[data-i18n="h1"]` y `button#langBtn` (`onclick="cycleLang()"`).
- [ ] **Step 3: anotar chrome estático** con `data-i18n` / `data-i18n-ph` / `data-i18n-title` (sub, textarea, botones, pasos, tarjetas, KPIs).
- [ ] **Step 4: CSS mínimo** `.brand` flex + `#langBtn` a la derecha (sin gradientes, sin hero, sin emojis).

### Task 3: Diccionario I18N + setLang

**Files:**
- Modify: `src/server.py` (apertura del `<script>`).

- [ ] **Step 1: `const I18N = {"es": {...}, "en": {...}}`** con las ~35 claves del chrome + mensajes dinámicos (`welcome`, `roi`, `perfect`, `example`, `valid_ok`, `blocked`, `sabmode`, `running`, `suite_head`, `suite_done`, `untracked`, `inv_demo`, `th_c`, `th_v`, `subtotal`, `iva`, `total`, `tx_yes`, `tx_no`, `ok`, `bad`, `pending`, `full`, `nosrc`, `s100`, `sok`).
- [ ] **Step 2: `t(k, vars)`** con reemplazo de `{placeholders}` y fallback a ES.
- [ ] **Step 3: `setLang(l)` / `cycleLang()`** — aplica `innerHTML`/`placeholder`/`title`, etiqueta del botón de envío según `step`, respeta el valor del textarea si el usuario ya escribió, persiste en `localStorage`, fija `document.documentElement.lang`.
- [ ] **Step 4: init** — `localStorage` primero, si no `navigator.language` (`en*` → inglés), `fmt` con locale según idioma.

### Task 4: Mensajes dinámicos vía `t()`

**Files:**
- Modify: `src/server.py` (cuerpos de `send`, `sabotage`, `runSuite`, `renderInvoice`, burbuja de bienvenida).

- [ ] **Step 1: welcome** → `bubble(t("welcome"),"ai")` después del init.
- [ ] **Step 2: `send()` paso 0** → `t("pending")`, `t("roi",{sav,src})`, `t("perfect",{n,sav,src,ex})`, `el.value = t("example")`, botón `t("gen")`.
- [ ] **Step 3: `send()` paso 1, `sabotage()`** → `t("valid_ok")` / `t("blocked")`, `t("sabmode")`.
- [ ] **Step 4: `runSuite()`** → `t("running")`, `t("s100")`, `t("sok")`, `t("suite_head",{p,p95})`, `t("suite_done",{p,p95})`.
- [ ] **Step 5: `renderInvoice()`** → `t("untracked")`, `t("inv_demo")`, `t("th_c")`, `t("th_v")`, `t("subtotal")`, `t("iva")`, `t("total")`, `t("tx_yes")`, `t("tx_no")`, `t("ok")`, `t("bad")`, `t("full")`, `t("nosrc")`.

### Task 5: Verificación

- [ ] **Step 1: compilar + suite completa**

Run: `python3 -m py_compile src/server.py && python3 -m unittest discover -s tests`
Expected: 6/6 OK (5 existentes + chrome).

- [ ] **Step 2: servir local y abrir en navegador** — comprobar toggle ES/EN, autodetección, favicon y marca; consola sin errores.

- [ ] **Step 3: dejar cambios sin commitear** para revisión del dueño (commit solo con orden expresa).
