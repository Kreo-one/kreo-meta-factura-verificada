# VOICE_EVIDENCE — demo-evidence-suite

## ponytail_decision
```json
{
  "rung_reached": "sdd-apply GREEN (T-1 test-primero 20/20, T-2 auditoria equivalente, T-3 deploy+verificacion)",
  "lines_written": 1,
  "lines_avoided": 0,
  "files": [
    "src/server.py",
    "openspec/changes/demo-evidence-suite/spec.md",
    "openspec/changes/demo-evidence-suite/tasks.md",
    "openspec/changes/demo-evidence-suite/premortem-research.md"
  ],
  "proof": {
    "smoke_local": "20/20 esperados, p95=2.5ms",
    "py_compile": "OK",
    "secret_sweep": "0 hits (sin claves en el slice; key solo por entorno Coolify)"
  },
  "constitution_safe": true
}
```

## caveman_report
```json
{
  "mode": "test-primero + auditoria equivalente + verificacion en vivo (el auditor PHP del skeleton no aplica a este repo Python)",
  "citations": [
    "suite-smoke.py (efimero): 20/20 OK contra localhost:18086",
    "python3 -m py_compile src/*.py: syntax OK",
    "grep secretos (PEM/gh[key]/sk-ant/API_KEY=valor): 0 hits",
    "spec.md Matriz I/O CASE-01..20 + CASE-FAIL; tasks.md 3/3 [x]"
  ],
  "evidence_complete": false,
  "evidence_gaps": [
    "Deploy Coolify + verificacion https en vivo (T-3, siguiente paso)",
    "Key Meta real ausente: planner en degradado honesto, sin teatro"
  ],
  "constitution_safe": true
}
```

## Cerebro (gbrain / engram)
Gap declarado: demo publico fuera del skeleton; sin MCP gbrain/engram expuesto en esta sesion. Estado fundamentado en archivos del repo (`openspec/changes/demo-evidence-suite/`, `src/server.py`) y salidas citadas arriba.
