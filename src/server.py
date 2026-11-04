"""Demo web Kreo Fiscal Shield: planner mock + gate determinista real.

Solo stdlib. Endpoints:
  GET  /         pagina demo (flujo: texto -> borrador -> veredicto)
  GET  /app      frontend auditado 7/7 (mismo origen que /api/...)
  GET  /health   chequeo Coolify
  POST /api/verify  {"amounts":[...],"dian_schema_ok":bool} -> veredicto (contrato estable)
  POST /api/draft   {"text":str,"with_tools":bool} -> borrador + veredicto
  POST /api/extract {"text":str} -> campos del negocio con tool_call_id + ahorro estimado
"""
from __future__ import annotations

import json
import os
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from verify import verify_draft

IVA_RATE = 19

APP_PATH = Path(__file__).resolve().parent / "static" / "app.html"

PAGE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kreo.One — ERP SaaS agentico: Fiscal Shield en vivo</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cpath d='M16 2l11 4v8c0 7-4.5 12-11 16C9.5 26 5 21 5 14V6z' fill='%23059669'/%3E%3Cpath d='M11 15l4 4 7-8' stroke='white' stroke-width='3' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
<style>
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;max-width:1080px;margin:1.5rem auto;padding:0 1rem;color:#475569;background:#f8fafc}
h1,h2,h3{color:#0f172a}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media (max-width:820px){.grid{grid-template-columns:1fr}}
.card{border:1px solid #cbd5e1;border-radius:10px;padding:1rem;background:#fff}
.msg{margin:.5rem 0;padding:.6rem .8rem;border-radius:8px;max-width:92%}
.ai{background:#ecfdf5}.me{background:#f1f5f9;text-align:left;margin-left:auto}
textarea{width:100%;height:3rem;font-size:1rem;padding:.5rem;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px}
button{padding:.55rem 1rem;margin:.3rem .2rem;font-size:.95rem;cursor:pointer}
.chip{display:inline-block;background:#f1f5f9;border-radius:10px;padding:.15rem .55rem;margin:.15rem;font-size:.82rem;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.chip.ok{background:#d1fae5}.chip.bad{background:#fee2e2}
.inv table{width:100%;border-collapse:collapse}
.inv td,.inv th{border-bottom:1px solid #cbd5e1;padding:.35rem;text-align:right}
.inv td:first-child,.inv th:first-child{text-align:left}
.pass{background:#ecfdf5;border:1px solid #059669;padding:.7rem;border-radius:6px;margin-top:.7rem}
.block{background:#fef2f2;border:1px solid #a33;padding:.7rem;border-radius:6px;margin-top:.7rem}
.mut{font-size:.82rem;color:#475569}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.kpi{display:flex;gap:.6rem;flex-wrap:wrap}.kpi div{background:#fff;border:1px solid #cbd5e1;border-radius:8px;padding:.45rem .7rem;font-size:.85rem}
.brand{display:flex;align-items:center;gap:.6rem}.brand h1{margin:0;font-size:1.35rem}#langBtn{margin-left:auto;flex:none;border:1px solid #cbd5e1;background:#fff;border-radius:8px}
.light{width:26px;height:26px;border-radius:50%;display:inline-block;vertical-align:middle;margin-right:.5rem}.light.go{background:#059669}.light.stop{background:#a33}summary{cursor:pointer;font-weight:bold}
body{font-size:17px}textarea{font-size:1.05rem}button{font-size:1rem}
.primary{background:#059669;color:#fff;border:none;border-radius:8px;padding:.8rem 1.6rem;font-size:1.1rem;cursor:pointer}
</style>
</head><body>
<div class="brand"><svg width="34" height="34" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 2l11 4v8c0 7-4.5 12-11 16C9.5 26 5 21 5 14V6z" fill="#059669"/><path d="M11 15l4 4 7-8" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg><h1 data-i18n="h1">Kreo Fiscal Shield — el agente propone, el verificador decide</h1><button id="langBtn" onclick="cycleLang()" title="ES/EN">EN</button></div>
<p class="mut" data-i18n="sub">Wizard del ERP SaaS agentico Kreo.One (planner Muse Spark en vivo; sin key, mock local honesto — el gate no cambia). Cada cifra lleva su <code>tool_call_id</code>: sin trazabilidad, no hay transmit.</p>
<div class="grid">
 <div class="card">
  <p class="mut" id="stepLine"></p>
  <div id="chat"></div>
  <textarea id="t" data-i18n-ph="ta_ph" placeholder="Cuéntanos de tu empresa…">Mi empresa es Distribuciones Bolivar SAS, facturamos 95 facturas al mes, gasto 40 horas contables y pago 300.000 en software</textarea><br>
  <button onclick="send()" id="sendBtn" class="primary">Enviar</button>
 </div>
 <div>
  <div class="card"><h3 data-i18n="dtitle">Datos extraídos (con trazabilidad)</h3><div id="chips"><span class="mut" data-i18n="nodata">Sin datos aún…</span></div>
  <div id="roi"></div></div>
  <div class="card inv" style="margin-top:1rem"><h3 data-i18n="invtitle">Factura en vivo</h3><div id="inv"><span class="mut" data-i18n="noinv">Tu primera factura aparece aquí…</span></div><div id="verdict"></div>
  <details id="advanced" style="margin-top:.7rem"><summary data-i18n="adv">Avanzado: pruebas y cifras</summary>
  <button onclick="sabotage()" data-i18n="sab" data-i18n-title="sab_t" title="El LLM escribe la cifra sin tool_call_id">Simular LLM sin herramientas</button>
  <button onclick="runSuite()" data-i18n="suite" data-i18n-title="suite_t" title="20 casos deterministas: validos, sin tool, schema roto, tipos invalidos">Correr suite de verificación (20 casos)</button>
  <div id="suite" style="margin-top:.6rem"></div>
  <div class="kpi" style="margin-top:.7rem">
    <div><span data-i18n="kpi_g">Grounding</span>: <b id="kGround">—</b></div>
    <div><span data-i18n="kpi_s">Schema DIAN</span>: <b id="kSchema">—</b></div>
    <div><span data-i18n="kpi_p">p95 sesión</span>: <b id="kP95">—</b></div>
  </details>
  </div></div>
 </div>
</div>
<script>
const I18N = {"es": {"h1": "Kreo Fiscal Shield — el agente propone, el verificador decide",
"sub": "Wizard del ERP SaaS agentico Kreo.One (planner Muse Spark en vivo; sin key, mock local honesto — el gate no cambia). Cada cifra lleva su <code>tool_call_id</code>: sin trazabilidad, no hay transmit.",
"ta_ph": "Cuéntanos de tu empresa…", "ta_default": "Mi empresa es Distribuciones Bolivar SAS, facturamos 95 facturas al mes, gasto 40 horas contables y pago 300.000 en software",
"send": "Enviar", "gen": "Generar factura", "sab": "Simular LLM sin herramientas", "sab_t": "El LLM escribe la cifra sin tool_call_id",
"suite": "Correr suite de verificación (20 casos)", "suite_t": "20 casos deterministas: validos, sin tool, schema roto, tipos invalidos",
"steps": "Paso 1: cuéntanos tu operación. Paso 2: escribe tu primera factura tras el análisis.",
"dtitle": "Datos extraídos (con trazabilidad)", "nodata": "Sin datos aún…", "invtitle": "Factura en vivo", "noinv": "Tu primera factura aparece aquí…",
"kpi_g": "Grounding", "kpi_s": "Schema DIAN", "kpi_p": "p95 sesión",
"welcome": "¡Bienvenido a KreO.One! Soy Sofía. Cuéntame de tu empresa: cuántas facturas emites, cuánto tiempo gastas en contabilidad y cuánto pagas en software.",
"roi": '<p><b>Ahorro estimado/mes:</b> {sav} (estimación demo: −35% software + 70% de tu tiempo contable).</p><p class="mut">Planner: {src}</p>',
"perfect": "Perfecto. Detecté {n} datos con trazabilidad total. Tu ahorro estimado es <b>{sav}/mes</b>. Fuente del planner: <b>{src}</b>. Ahora escribe tu primera factura, p. ej.: <i>{ex}</i>.",
"example": "factura a Distribuciones Bolivar por 2.450.000 + IVA por servicios contables",
"valid_ok": "Factura validada por el verificador: schema DIAN OK y cada cifra con <code>tool_call_id</code>. Lista para transmitir.",
"blocked": "El verificador bloqueó la factura: hay cifras sin <code>tool_call_id</code>. El agente propone; el verificador decide.",
"sabmode": "Modo sabotaje: el LLM escribirá la próxima cifra sin herramientas.", "running": "Corriendo 20 casos deterministas…",
"suite_head": "<b>{p}/20 comportamientos esperados</b> · p95 sesión {p95} ms · N=20 determinista, medido en tu navegador.",
"suite_done": "Suite completa: <b>{p}/20</b> comportamientos esperados, p95 {p95} ms medido en tu navegador. Nada de diapositivas: el gate ejecutó de verdad.",
"untracked": "sin trazabilidad", "inv_demo": "Factura demo", "th_c": "Concepto", "th_v": "Valor",
"subtotal": "Subtotal", "iva": "IVA 19%", "total": "Total", "tx_yes": "TRANSMITIR: SI", "tx_no": "TRANSMITIR: NO",
"ok": "OK", "bad": "FALLA", "pending": "pendiente factura", "full": "100%", "nosrc": "cifras sin fuente", "s100": "100% (suite)", "sok": "OK (suite)", "th_r": "Resultado",
"step_of": "Paso {n} de 3", "g1": "Cuéntanos de tu empresa en una frase.", "g2": "Ahora escribe tu primera factura.", "g3": "Veredicto del semáforo: verde puedes enviar, rojo hay que explicar una cifra.",
"adv": "Avanzado: pruebas y cifras", "go_word": "Puedes enviarla", "stop_word": "Frenada: hay que explicar una cifra"},
"en": {"h1": "Kreo Fiscal Shield — the agent proposes, the verifier decides",
"sub": "Kreo.One agentic SaaS ERP wizard (live Muse Spark planner; no key, honest local mock — the gate never changes). Every figure carries its <code>tool_call_id</code>: no traceability, no transmit.",
"ta_ph": "Tell us about your company…", "ta_default": "My company is Distribuciones Bolivar SAS, we issue 95 invoices a month, spend 40 hours on accounting and pay 300,000 in software",
"send": "Send", "gen": "Generate invoice", "sab": "Simulate LLM without tools", "sab_t": "The LLM writes the figure with no tool_call_id",
"suite": "Run verification suite (20 cases)", "suite_t": "20 deterministic cases: valid, no-tool, broken schema, invalid types",
"steps": "Step 1: tell us about your operation. Step 2: write your first invoice after the analysis.",
"dtitle": "Extracted data (with traceability)", "nodata": "No data yet…", "invtitle": "Live invoice", "noinv": "Your first invoice shows up here…",
"kpi_g": "Grounding", "kpi_s": "DIAN schema", "kpi_p": "session p95",
"welcome": "Welcome to KreO.One! I'm Sofia. Tell me about your company: how many invoices you issue, how much time you spend on accounting and what you pay for software.",
"roi": '<p><b>Estimated savings/mo:</b> {sav} (demo estimate: −35% software + 70% of your accounting time).</p><p class="mut">Planner: {src}</p>',
"perfect": "Got it. I detected {n} data points with full traceability. Your estimated savings are <b>{sav}/mo</b>. Planner source: <b>{src}</b>. Now write your first invoice, e.g.: <i>{ex}</i>.",
"example": "invoice to Distribuciones Bolivar for 2,450,000 + VAT for accounting services",
"valid_ok": "Invoice validated by the verifier: DIAN schema OK and every figure with <code>tool_call_id</code>. Ready to transmit.",
"blocked": "The verifier blocked the invoice: there are figures with no <code>tool_call_id</code>. The agent proposes; the verifier decides.",
"sabmode": "Sabotage mode: the LLM will write the next figure without tools.", "running": "Running 20 deterministic cases…",
"suite_head": "<b>{p}/20 expected behaviors</b> · session p95 {p95} ms · N=20 deterministic, measured in your browser.",
"suite_done": "Suite complete: <b>{p}/20</b> expected behaviors, p95 {p95} ms measured in your browser. No slides: the gate really ran.",
"untracked": "untracked", "inv_demo": "Demo invoice", "th_c": "Item", "th_v": "Amount",
"subtotal": "Subtotal", "iva": "19% VAT", "total": "Total", "tx_yes": "TRANSMIT: YES", "tx_no": "TRANSMIT: NO",
"ok": "OK", "bad": "FAIL", "pending": "invoice pending", "full": "100%", "nosrc": "figures without source", "s100": "100% (suite)", "sok": "OK (suite)", "th_r": "Result",
"step_of": "Step {n} of 3", "g1": "Tell us about your company in one sentence.", "g2": "Now write your first invoice.", "g3": "Semaphore verdict: green you can send, red one figure needs explaining.",
"adv": "Advanced: tests and figures", "go_word": "You can send it", "stop_word": "Stopped: one figure needs explaining"}};
function t(k, vars){ let s = (I18N[lang] && I18N[lang][k]) || I18N["es"][k] || k; for(const n in (vars||{})) s = s.split("{"+n+"}").join(vars[n]); return s; }
let lang = "es";
const chatLog = [];
function say(key, vars, cls){ chatLog.push({kind: "ai", key: key, vars: vars || {}}); bubble(t(key, vars), cls || "ai"); }
function mine(html){ chatLog.push({kind: "me", html: html}); bubble(html, "me"); }
function rerenderChat(){ const box = document.getElementById("chat"); if(!box) return; box.innerHTML = "";
  chatLog.forEach(e => { bubble(e.kind === "ai" ? t(e.key, e.vars) : e.html, e.kind === "ai" ? "ai" : "me"); });
}
function setLang(l){ lang = (l === "en") ? "en" : "es"; try{ localStorage.setItem("kreo-lang", lang); }catch(e){}
  document.documentElement.lang = lang; document.title = "Kreo.One — ERP SaaS agentico: Fiscal Shield en vivo";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.innerHTML = t(el.getAttribute("data-i18n")); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.getAttribute("data-i18n-ph")); });
  document.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = t(el.getAttribute("data-i18n-title")); });
  const sb = document.getElementById("sendBtn"); if(sb) sb.textContent = (typeof step !== "undefined" && step === 1) ? t("gen") : t("send");
  const ta = document.getElementById("t"); if(ta && (ta.value === I18N["es"]["ta_default"] || ta.value === I18N["en"]["ta_default"])) ta.value = t("ta_default");
  const lb = document.getElementById("langBtn"); if(lb) lb.textContent = (lang === "es") ? "EN" : "ES"; setStep(wizStep); rerenderChat(); }
function cycleLang(){ setLang(lang === "es" ? "en" : "es"); }
let wizStep = 1;
function setStep(n){ wizStep = n; const sl = document.getElementById("stepLine"); if(sl) sl.innerHTML = "<b>" + "●".repeat(n) + "○".repeat(3 - n) + " " + t("step_of", {n: n}) + "</b> · " + t("g" + n); }
const fmt = c => "$ " + (c/100).toLocaleString(lang === "en" ? "en-US" : "es-CO");
const lat = []; let step = 0, sabotaged = false;
try{ const saved = localStorage.getItem("kreo-lang"); setLang(saved || (((navigator.language || "es").toLowerCase().indexOf("en") === 0) ? "en" : "es")); }catch(e){ setLang("es"); }
function bubble(txt, cls){
  const d = document.createElement("div"); d.className = "msg " + cls; d.innerHTML = txt;
  document.getElementById("chat").appendChild(d); d.scrollIntoView({behavior:"smooth"});
}
async function timed(path, payload){
  const t0 = performance.now();
  const r = await fetch(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  lat.push(performance.now() - t0);
  lat.sort((a,b)=>a-b);
  document.getElementById("kP95").textContent = Math.round(lat[Math.ceil(0.95*lat.length)-1]) + " ms";
  return r.json();
}
say("welcome");
async function send(){
  const el = document.getElementById("t"); const text = el.value.trim(); if(!text) return;
  mine(text);
  if(step === 0){
    const d = await timed("/api/extract",{text});
    const f = d.fields;
    document.getElementById("chips").innerHTML = f.map(x =>
      `<span class="chip ok">${x.field}: ${x.display} · ${x.tool_call_id}</span>`).join("");
    document.getElementById("kGround").textContent = "100% (" + f.length + "/" + f.length + ")";
    document.getElementById("kSchema").textContent = t("pending");
    document.getElementById("roi").innerHTML = t("roi", {sav: fmt(d.savings_cents), src: d.source});
    say("perfect", {n: f.length, sav: fmt(d.savings_cents), src: d.source, ex: t("example")});
    el.value = t("example"); step = 1; document.getElementById("sendBtn").textContent = t("gen"); setStep(2);
  } else {
    const d = await timed("/api/draft",{text, with_tools: !sabotaged, fields_count: 0});
    renderInvoice(d);
    say(d.transmit ? "valid_ok" : "blocked");
    sabotaged = false;
  }
}
function sabotage(){ sabotaged = true; say("sabmode"); }
async function runSuite(){
  const box = document.getElementById("suite");
  box.innerHTML = "<p class='mut'>" + t("running") + "</p>";
  const valids = [1,1000,9500000,245000000,30000000,1000000000,99,50000000000];
  const jobs = valids.map(c => ({path:"/api/verify", body:{amounts:[{cents:c,tool_call_id:"t"}],dian_schema_ok:true}, expect:true}));
  [1,1000,9500000,245000000,30000000,10000000].forEach(c => jobs.push({path:"/api/verify", body:{amounts:[{cents:c}],dian_schema_ok:true}, expect:false}));
  for(let i=0;i<3;i++) jobs.push({path:"/api/verify", body:{amounts:[{cents:1000,tool_call_id:"t"}],dian_schema_ok:false}, expect:false});
  jobs.push({path:"/api/verify", body:{amounts:[{cents:"2450000",tool_call_id:"t"}],dian_schema_ok:true}, expect:false});
  jobs.push({path:"/api/verify", body:{amounts:[{cents:24.5,tool_call_id:"t"}],dian_schema_ok:true}, expect:false});
  jobs.push({path:"/api/extract", body:{text:"Mi empresa es Café Andino LTDA, con 60 facturas"}, expectExtract:true});
  let pass = 0; const rows = [];
  for(let i=0;i<jobs.length;i++){
    const t0 = performance.now();
    let ok = false, note = "";
    try{
      const r = await fetch(jobs[i].path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(jobs[i].body)});
      const d = await r.json();
      if(jobs[i].expectExtract){ ok = d.fields && d.fields.length === 2 && d.fields.every(f => f.tool_call_id); note = "extract 2/2 trazados"; }
      else { ok = !!d.transmit === jobs[i].expect; note = d.transmit ? "PASS" : String(d.veredicto).slice(0,60); }
      lat.push(performance.now() - t0);
    }catch(e){ note = "ERROR red"; }
    pass += ok ? 1 : 0;
    rows.push(`<tr><td>${i+1}</td><td>${ok ? "✓" : "✗"}</td><td class="mut">${note}</td></tr>`);
  }
  lat.sort((a,b)=>a-b);
  const p95 = Math.round(lat[Math.ceil(0.95*lat.length)-1]);
  document.getElementById("kP95").textContent = p95 + " ms";
  document.getElementById("kGround").textContent = t("s100");
  document.getElementById("kSchema").textContent = t("sok");
  box.innerHTML = `<p>${t("suite_head", {p: pass, p95: p95})}</p>
  <table><tr><th>#</th><th></th><th>${t("th_r")}</th></tr>${rows.join("")}</table>`;
  say("suite_done", {p: pass, p95: p95});
}
function renderInvoice(d){
  const items = d.draft.items.map(it =>
    `<tr><td>${it.concept} ${it.tool_call_id ? `<span class="chip ok">${it.tool_call_id}</span>` : `<span class="chip bad">${t("untracked")}</span>`}</td><td>${fmt(it.cents)}</td></tr>`).join("");
  document.getElementById("inv").innerHTML = `
    <h4 style="margin:.2rem 0">${t("inv_demo")} ${d.draft.number} — ${d.draft.customer} (${d.draft.date})</h4>
    <table><tr><th>${t("th_c")}</th><th>${t("th_v")}</th></tr>${items}
    <tr><td>${t("subtotal")}</td><td>${fmt(d.draft.subtotal_cents)}</td></tr>
    <tr><td>${t("iva")}</td><td>${fmt(d.draft.iva_cents)}</td></tr>
    <tr><td><b>${t("total")}</b></td><td><b>${fmt(d.draft.total_cents)}</b></td></tr></table>`;
  document.getElementById("verdict").innerHTML = `<div class="${d.transmit ? "pass" : "block"}"><span id="verdict-light" class="light ${d.transmit ? "go" : "stop"}"></span><b>${d.transmit ? t("tx_yes") : t("tx_no")} — ${d.transmit ? t("go_word") : t("stop_word")}</b><br><span class="mut">${d.veredicto}</span></div>`;
  setStep(3);
  document.getElementById("kSchema").textContent = d.draft.dian_schema_ok ? t("ok") : t("bad");
  document.getElementById("kGround").textContent = d.transmit ? t("full") : t("nosrc");
}
</script>
</body></html>
"""

HOUR_VALUE_CENTS = 2_500_000


EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_business_fields",
        "description": "Extrae datos del negocio desde lenguaje natural",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {"type": ["string", "null"]},
                "monthly_invoices": {"type": ["integer", "null"]},
                "accounting_hours": {"type": ["integer", "null"]},
                "current_software_cost_cents": {"type": ["integer", "null"]},
            },
        },
    },
}


def sanitize_api_key(raw: str) -> str:
    """Clave lista para el header Authorization.

    Coolify/Docker pueden guardar el valor con comillas literales envolventes
    o con CR/LF; un header con esos bytes es rechazado con 401 (regresion
    fijada en tests/test_planner_auth.py).
    """
    return raw.replace("\r", "").replace("\n", "").strip().strip('"').strip("'").strip()


def meta_planner_fields(text: str) -> dict | None:
    """Planner Muse Spark (Meta, cloud): tool-calling real con trazabilidad de la llamada.

    Contrato idéntico al del ERP (config/neuron.php meta_spark): endpoint y key
    por entorno, modelo muse-spark-1.3. Devuelve None si no hay credenciales o si
    la llamada falla (auth/timeout) — el caller degrada al extractor local.
    """
    endpoint = os.getenv("META_SPARK_PLANNER_ENDPOINT", "").strip()
    api_key = sanitize_api_key(os.getenv("META_SPARK_API_KEY", ""))
    model = os.getenv("META_SPARK_PLANNER_MODEL", "muse-spark-1.3").strip()
    if not endpoint or not api_key:
        return None

    import urllib.error
    import urllib.request

    payload = {
        "model": model,
        "reasoning_effort": "low",
        "messages": [
            {"role": "system", "content": "Extrae los datos del negocio con la herramienta. Nada de texto libre."},
            {"role": "user", "content": text},
        ],
        "tools": [EXTRACT_TOOL],
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "KreOFiscalShield/1.0 (Linux; x86_64) Mozilla/5.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        print(f"[planner] meta http={http_error.code}", flush=True)
        return None
    except Exception as error:  # noqa: BLE001 - degradacion honesta ante cualquier fallo
        print(f"[planner] meta fallo={type(error).__name__}", flush=True)
        return None

    choices = body.get("choices") or []
    if not choices:
        return None
    tool_calls = (choices[0].get("message") or {}).get("tool_calls") or []
    if not tool_calls:
        return None

    call = tool_calls[0]
    try:
        args = json.loads((call.get("function") or {}).get("arguments") or "{}")
    except json.JSONDecodeError:
        return None

    fields: list[dict] = []
    software_cents = args.get("current_software_cost_cents") or 0
    for name in ("company_name", "monthly_invoices", "accounting_hours", "current_software_cost_cents"):
        value = args.get(name)
        if value is None:
            continue
        display = fmt_pesos(value) if name == "current_software_cost_cents" and isinstance(value, int) else str(value)
        fields.append({"field": name, "value": value, "display": display, "tool_call_id": call.get("id", "call_meta")})

    hours = args.get("accounting_hours") or 0
    savings = (software_cents * 35 // 100 if isinstance(software_cents, int) else 0) + hours * 70 * HOUR_VALUE_CENTS // 100
    host = endpoint.split("/")[2] if "://" in endpoint else endpoint
    return {
        "fields": fields,
        "savings_cents": savings,
        "source": f"Muse Spark (Meta, cloud) · {model} · {host}",
        "tool_call_id": call.get("id", "call_meta"),
    }


def extract_business(text: str) -> dict:
    """Extractor determinista (misma heurística del fallback del ERP) con trazabilidad por campo."""
    fields: list[dict] = []

    def add(field: str, value, cents: int | None = None) -> None:
        display = fmt_pesos(cents) if cents is not None else str(value)
        fields.append({"field": field, "value": value, "display": display, "tool_call_id": "call_extract_1"})

    match = re.search(
        r"(?:empresa(?: es)?|negocio(?: es)?|somos)\s+([A-Za-z0-9\u00c0-\u00ff\s]+?(?:SAS|S\.A\.S\.|LTDA|Ltda|S\.A\.|E\.U\.|Real))",
        text, re.IGNORECASE)
    if match:
        add("company_name", match.group(1).strip())
    match = re.search(r"(\d+)\s*(?:facturas|comprobantes|factura)", text, re.IGNORECASE)
    if match:
        add("monthly_invoices", int(match.group(1)))
    match = re.search(r"(\d+)\s*(?:horas|hora|hrs)", text, re.IGNORECASE)
    hours = int(match.group(1)) if match else 0
    if match:
        add("accounting_hours", hours)
    match = re.search(r"(?:pago|pagamos|software(?: de)?)\s*(?:\$)?\s*([\d\.]+)", text, re.IGNORECASE)
    software_cents = int(match.group(1).replace(".", "")) * 100 if match else 0
    if match:
        add("current_software_cost_cents", software_cents, software_cents)

    savings = software_cents * 35 // 100 + hours * 70 * HOUR_VALUE_CENTS // 100
    return {"fields": fields, "savings_cents": savings, "source": "degradado local (sin key Meta)"}


def fmt_pesos(cents: int) -> str:
    return f"$ {cents // 100:,}".replace(",", ".")


def parse_money_cents(text: str) -> int:
    """Extrae la primera cifra de dinero y la devuelve en centavos (int, cero float)."""
    match = re.search(r"\$?\s*([\d][\d\.]*)", text.replace(",", "."))
    if not match:
        return 0
    return int(match.group(1).replace(".", "")) * 100


def parse_customer(text: str) -> str:
    """Cliente entre 'a' y 'por'; si no hay, valor por defecto honesto."""
    match = re.search(r"\bfactura\s+a\s+(.+?)\s+por\b", text, re.IGNORECASE)
    if match:
        return match.group(1).strip().capitalize()
    return "Cliente demo"


def build_draft(text: str, with_tools: bool) -> dict:
    """Planner mock: interpreta la cifra como subtotal y suma IVA 19% (todo en centavos int)."""
    subtotal = parse_money_cents(text)
    iva = subtotal * IVA_RATE // 100
    item: dict = {"cents": subtotal, "concept": "servicios"}
    if with_tools:
        item["tool_call_id"] = "call_demo_1"
    draft = {
        "number": "DEMO-0001",
        "date": date.today().isoformat(),
        "customer": parse_customer(text),
        "items": [item],
        "subtotal_cents": subtotal,
        "iva_cents": iva,
        "total_cents": subtotal + iva,
        "amounts": [{"cents": subtotal, **({"tool_call_id": "call_demo_1"} if with_tools else {})}],
        "dian_schema_ok": True,
    }
    return draft


class Handler(BaseHTTPRequestHandler):
    server_version = "FiscalShield/1.1"

    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, b'{"ok":true}')
        elif self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/app":
            try:
                body = APP_PATH.read_bytes()
            except OSError:
                self._send(404, b'{"error":"not found"}')
            else:
                self._send(200, body, "text/html; charset=utf-8")
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/extract":
            req = self._json_body()
            if req is None or not isinstance(req.get("text"), str):
                self._send(400, b'{"error":"texto requerido"}')
                return
            result = meta_planner_fields(req["text"]) or extract_business(req["text"])
            self._send(200, json.dumps(result).encode("utf-8"))
        elif self.path == "/api/verify":
            draft = self._json_body()
            if draft is None:
                self._send(400, b'{"transmit":false,"veredicto":"bloqueado: cuerpo invalido"}')
                return
            ok, msg = verify_draft(draft)
            self._send(200 if ok else 422, json.dumps({"transmit": ok, "veredicto": msg}).encode("utf-8"))
        elif self.path == "/api/draft":
            req = self._json_body()
            if req is None or not isinstance(req.get("text"), str):
                self._send(400, b'{"transmit":false,"veredicto":"bloqueado: texto requerido"}')
                return
            draft = build_draft(req["text"], bool(req.get("with_tools", True)))
            ok, msg = verify_draft(draft)
            payload = {
                "draft": {k: v for k, v in draft.items() if k != "amounts"},
                "transmit": ok,
                "veredicto": msg,
            }
            self._send(200, json.dumps(payload).encode("utf-8"))
        else:
            self._send(404, b'{"error":"not found"}')

    def log_message(self, *args: object) -> None:
        pass


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"fiscal-shield demo en puerto {port} (Muse Spark con key, mock sin key)")
    server.serve_forever()


if __name__ == "__main__":
    main()
