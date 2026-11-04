# Submission text — English (copy-paste source of truth)

> **KreO.One — Fiscal Shield (Agentic Module for SME ERP)**
> **Platform context:** Private ERP SaaS in production (Laravel + Filament, DDD/EDA architecture, PostgreSQL 16, deployed on Coolify/Docker).
> **Hackathon deliverable (this repo + live demo at [https://factura.kreo.lat](https://factura.kreo.lat)):**
> Agentic invoicing microservice with zero numeric hallucinations, integrated with **Meta (Muse Spark 1.3)** models via OpenAI-compatible contract with native Tool Calling.
> **Guardrail mechanism (Fiscal Shield):**
> • **Planner:** Builds the draft solely through structured tool calls (includes a local deterministic fallback if the external API degrades; the page labels it).
> • **Verifier:** Deterministic filter that live-blocks any figure without a traceable `tool_call_id` and validates the structure against DIAN numeric rules in integers (cents, zero floats) before rendering.
> • **Live demo:** Conversational wizard → invoice rendered in real time → frontend-integrated test suite (20 deterministic cases with pass-rate and measured p95: ≈0.3–0.5s in production).
> • **Scope:** DIAN electronic invoicing (Colombia): 19% VAT, COP cents, pre-transmit validation.
> • **Framework:** Decrees 2242/2015 and 358/2020; DIAN Res. 042/2020 and 165/2023 (design reference; demo with no real transmit or tax validity).

Notes for the human (do not paste): do not mention Llama 3, Baseten, Workers, SHA-256 or XML/XSD (no evidence in this repo); no self-assigned scores; quoted p95 is the one measured by `scripts/post-deploy-check.py --full` against production.
