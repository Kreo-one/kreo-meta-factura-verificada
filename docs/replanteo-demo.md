# Replanteo del demo — Kreo Fiscal Shield (Meta Global AI Developer Hackathon)

## 1. Diagnóstico del demo anterior

La versión inicial (dos botones que imprimen JSON) no compite: no se entiende sin explicación, no hay producto visible, no hay historia. Frente a 2.000+ proyectos, un veredicto en texto plano no genera memoria ni diferenciación.

## 2. Historia aprobada (Opción 1 + Opción 3)

**"El agente propone. El verificador decide."**

Kreo.One es un ERP SaaS agéntico para PYMEs colombianas. Su diferenciador no es generar facturas —eso lo hace cualquiera— sino **que el modelo jamás puede escribir una cifra sin trazabilidad**: cada número del borrador referencia el `tool_call_id` que lo produjo. Sin esa referencia, el sistema bloquea la transmisión antes de tocar la DIAN.

El demo debe mostrar en 90 segundos:

1. Una conversación natural ("facturo 95 facturas al mes, pago $300.000 en software…") que el agente convierte en datos estructurados, cifra por cifra, cada una con su fuente visible.
2. La primera factura electrónica generándose en vivo, con schema DIAN validado.
3. El momento anti-alucinación: el mismo agente, sin herramientas, intenta escribir la cifra —y el gate lo bloquea en pantalla.

Opción 3 (respaldo): el video puede cortar 5 segundos al ERP real en staging (panel del wizard de KreO.One) para probar que esto no es una maqueta: es un módulo de un producto vivo. El core permanece privado; solo se muestra UI.

## 3. Superficie (aprobada: chat wizard + factura en vivo)

- **Izquierda:** chat paso a paso con Sofía (init → descubrimiento → ahorro → primera factura), reflejando el wizard real del ERP (`CommercialWizardPage`).
- **Derecha:** la factura que se construye en vivo: cliente, ítems, subtotal, IVA 19%, total — cada cifra con su `tool_call_id` en chip.
- **Panel de verificación:** grounding, schema DIAN y latencia medida en la sesión.
- **Botón de sabotaje:** "simular LLM sin herramientas" para ver el bloqueo en vivo.

## 4. Criterios de éxito (medibles, SaaS-S)

| KPI | Definición | Cómo se evidencia |
|---|---|---|
| KPI-1 Grounding | 100% de cifras con `tool_call_id`; 0 escritas por el modelo | Chips por cifra + caso bloqueado |
| KPI-2 Schema DIAN | 100% de borradores con schema válido antes de transmitir | Sello "schema DIAN OK" en el borrador |
| KPI-3 Latencia | p95 < 3s de texto a borrador | Medidor de sesión en el panel |

## 5. Honestidad del demo

El planner corre como mock determinista local (etiquetado en pantalla). Con `META_MODEL_API_KEY` el mismo contrato llama a Muse Spark; **el gate no cambia**. Sin key, el sistema degrada con gracia —que es exactamente lo que el ERP hace en producción (fallback `CloudflareWizardAiService` → heurística).

## 6. Riesgos

- **Key Meta suspendida** (COP$30.031 impago): mitiga el fallback; el demo no depende de ella.
- **Staging en loop de restart:** la toma del ERP real depende de recuperar `staging-app`; el demo público no depende de staging.
- **Deadline 4 nov 21:00 ET:** el demo público es autónomo y ya está desplegado; esta mejora es incremental sobre esa URL.

## 7. Video (guión de 90 s)

1. (0-10s) Problema: "una IA que inventa una cifra en tu factura electrónica te mete en problemas con la DIAN".
2. (10-45s) Conversación → datos con trazabilidad → ahorro estimado.
3. (45-75s) Primera factura en vivo + sello schema DIAN.
4. (75-90s) Sabotaje: LLM sin herramientas → **BLOQUEADO**. Cierre: "El agente propone. El verificador decide."
