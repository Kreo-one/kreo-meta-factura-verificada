# MUSE.md — Kreo Fiscal Shield

Agentic invoicing guardrail for Colombia (DIAN electronic invoicing).
Built and audited with **Muse Code, powered by Meta Muse Spark**.

## The one rule

The agent proposes, the verifier decides: no figure transmits without a
`tool_call_id`, and DIAN schema must validate first. See `src/verify.py`.

## Contracts (stable)

- `GET /`, `/app` — audited frontend (ES/EN + light/dark, zero CDN)
- `GET /health` — Coolify check
- `POST /api/extract` `{"text"}` → fields + `tool_call_id` + savings
- `POST /api/draft` `{"text","with_tools"}` → draft + `{transmit, veredicto}`
- `POST /api/verify` → `200` transmit / `422` blocked

Full LLM contract: [docs/LLM_CONTRACT.md](docs/LLM_CONTRACT.md).
Conventions and test command: [AGENTS.md](AGENTS.md).

## Verify

```
python3 -m unittest discover -s tests   # 17 tests, must stay green
python3 scripts/post-deploy-check.py --full https://factura.kreo.lat
```
