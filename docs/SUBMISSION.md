# Texto de submission — Cerebral Valley (fuente de verdad, copiar-pegar)

> **KreO.One — Fiscal Shield (Módulo Agéntico para ERP PyME)**
> **Contexto de Plataforma:** ERP SaaS privado en producción (Laravel + Filament, arquitectura DDD/EDA, PostgreSQL 16, desplegado en Coolify/Docker).
> **Entregable Hackathon (Este Repo + Demo en [https://factura.kreo.lat](https://factura.kreo.lat)):**
> Microservicio agéntico de facturación sin alucinaciones numéricas integrado con modelos **Meta (Muse Spark 1.3)** mediante contrato OpenAI-compatible con Tool Calling nativo.
> **Mecanismo de Guardrail (Fiscal Shield):**
> • **Planner:** Construye el borrador únicamente mediante llamadas a herramientas estructuradas (incluye fallback determinista local si la API externa degrada; la página lo etiqueta).
> • **Verifier:** Filtro determinista que bloquea en vivo cualquier cifra sin `tool_call_id` trazable y valida la estructura contra las reglas numéricas DIAN en enteros (centavos, cero flotantes) antes de renderizar.
> • **Demo en Vivo:** Wizard conversacional → Factura renderizada en tiempo real → Suite de pruebas integrada en frontend (20 casos deterministas con pass-rate y p95 medido: ≈0.3–0.5s en producción).

Notas para el humano (no pegar): no mencionar Llama 3, Baseten, Workers, SHA-256 ni XML/XSD (sin evidencia en este repo); no dar puntajes auto-asignados; p95 citado es el medido por `scripts/post-deploy-check.py --full` contra producción.
