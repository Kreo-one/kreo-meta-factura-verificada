# LLM Contract — Muse Spark planner (Meta)

Single source of truth for how the repo talks to the LLM. The verifier never
trusts the model: every figure the planner returns must carry a `tool_call_id`,
or the gate blocks transmit.

## Transport

- Endpoint: `$META_SPARK_PLANNER_ENDPOINT` (OpenAI-compatible chat-completions).
- Auth: `Authorization: Bearer $META_SPARK_API_KEY`, sanitized
  (`sanitize_api_key`: strips wrapping quotes and CR/LF — see the 401 regression
  test in `tests/test_planner_auth.py`).
- Model: `$META_SPARK_PLANNER_MODEL`, default `muse-spark-1.3`.
- `reasoning_effort: "low"`, timeout 8 s, `User-Agent: KreOFiscalShield/1.0`.

## Tool

One tool, `extract_business_fields`:

| Arg | Type |
|---|---|
| `company_name` | string \| null |
| `monthly_invoices` | integer \| null |
| `accounting_hours` | integer \| null |
| `current_software_cost_cents` | integer \| null |

Money is always integer cents. The system message forces tool use
("extrae con la herramienta, nada de texto libre").

## Message flow (`meta_planner_fields` in `src/server.py`)

1. `POST /api/extract {"text": "..."}` arrives.
2. Server sends `system + user(text) + tools[extract_business_fields]`.
3. It reads `choices[0].message.tool_calls[0]`; on any anomaly
   (no credentials, HTTP error, timeout, bad JSON, empty `tool_calls`) it
   returns `None`.
4. The call `id` becomes every field's `tool_call_id`; savings are computed
   deterministically: 35% of software cost + 70% of accounting hours valued
   at `$25.000`/h (`HOUR_VALUE_CENTS`).
5. `None` degrades to the local regex extractor (`extract_business`),
   labeled `"degradado local (sin key Meta)"` with `tool_call_id "call_extract_1"`.

## Gate input

The draft carries `amounts: [{cents: int, tool_call_id}]` plus
`dian_schema_ok`. `verify_draft` (`src/verify.py`) transmits only if every
cent is an `int` with a `tool_call_id` and the DIAN schema flag is set.

## Env vars (single scheme)

| Var | Used by |
|---|---|
| `META_SPARK_PLANNER_ENDPOINT` | `src/server.py` |
| `META_SPARK_API_KEY` | `src/server.py`, `src/agent.py` (presence check) |
| `META_SPARK_PLANNER_MODEL` | `src/server.py` (default `muse-spark-1.3`) |

`src/agent.py` is a thin offline CLI demo: it never hits the network, it
builds a hardcoded draft and runs the gate locally.
