# Especificación de Documentos Tier-3 (D16–D23)

**Propósito**: extender el corpus de Nexus Soluciones S.A.C. con material que justifique el carácter *local/offline* del chatbot. A diferencia de los D01–D15 (políticas employee-facing, Tier-1/2), los siguientes contienen información **comercial, técnica y financiera confidencial** que ninguna empresa sensata enviaría a un LLM en la nube.

**Convenciones**: se mantiene el estilo de los D01–D15 (encabezado con código, versión, fecha, propietario; ~5–7 páginas; redacción formal peruana; referencias cruzadas internas). Toda la data es sintética pero internamente consistente con `nexus_ground_truth.json`.

---

## D16 — Modelo de Pricing y Tarifario Profesional por Seniority

- **Código**: COMERCIAL-POL-001
- **Versión**: 5.2 | **Fecha**: Enero 2026
- **Propietario**: Gerencia Comercial — Carlos Amat y León Ríos
- **Clasificación**: CONFIDENCIAL — Uso interno restringido (Comercial + Dirección)

### Secciones
1. Estructura de tarifas hora por rol y seniority (matriz Junior / Semi-Senior / Senior / Lead / Architect × Desarrollador / QA / PM / Consultor / Arquitecto), en S/. y USD.
2. Costo total interno (CTC) por rol — base para cálculo de margen bruto.
3. Margen mínimo aceptable por modalidad: T&M 38%, Fixed Price 42%, Staff Augmentation 28%.
4. Política de descuentos autorizados: hasta 5% Gerente Comercial, 5–10% CEO, >10% Directorio.
5. Premium por industria regulada: Banca +15%, Salud +12%, Seguros +10%.
6. Tarifas fuera de horario, fines de semana y emergencias (recargo 50% / 100% / 150%).
7. Ciclo de revisión anual de tarifas (enero) y triggers de revisión extraordinaria.

### Datos sensibles a incluir
Tarifas exactas, CTC interno, márgenes objetivo, niveles de autoridad de descuento.

---

## D17 — Playbook de Propuestas Comerciales y Respuesta a RFP

- **Código**: COMERCIAL-PROC-001
- **Versión**: 3.0 | **Fecha**: Febrero 2026
- **Propietario**: Gerencia Comercial
- **Clasificación**: CONFIDENCIAL — Uso interno

### Secciones
1. Pipeline comercial estandarizado: Lead → Qualify → Discovery → Propuesta → Negociación → Cierre → Handoff a Delivery.
2. SLA interno de respuesta a RFP: 5 días hábiles para propuestas <S/. 200k, 10 días para mayores.
3. Plantilla obligatoria de propuesta: resumen ejecutivo, entendimiento, enfoque, equipo, cronograma, inversión, supuestos.
4. Matriz Go/No-Go con 8 criterios ponderados (encaje técnico, margen estimado, riesgo país/cliente, capacidad disponible, etc.).
5. Aprobaciones por monto: hasta S/. 100k Gerente Comercial, S/. 100k–500k CEO, >S/. 500k Directorio.
6. Red flags contractuales: penalidades >10% del contrato, transferencia de IP irrestricta, jurisdicción extranjera sin arbitraje.
7. Tres casos sintéticos de lessons learned de propuestas perdidas (con causa raíz).

---

## D18 — Cartera de Clientes Activos y Maestro de Contratos

- **Código**: COMERCIAL-REG-001
- **Versión**: 4.1 | **Fecha**: Marzo 2026 (actualización trimestral)
- **Propietario**: Gerencia Comercial + CFO
- **Clasificación**: ESTRICTAMENTE CONFIDENCIAL — Acceso por NDA

### Secciones
1. Top 10 clientes con: nombre, sector, contrato anual en S/., sponsor ejecutivo Nexus, fecha de inicio, fecha de renovación.
2. Concentración de ingresos: % por cliente y por sector — alerta si un cliente >25%.
3. SLA contractual por cliente (uptime, tiempos de respuesta, penalidades).
4. NDAs activos: contraparte, alcance, fecha de vencimiento.
5. Contratos en negociación (pipeline ponderado).
6. Riesgos comerciales abiertos: clientes morosos, renovaciones en riesgo, disputas activas.
7. Plan de retención por cuenta estratégica.

### Datos sensibles
Nombres de clientes (ficticios pero realistas), montos exactos, fechas, SLAs, penalidades.

---

## D19 — Arquitecturas de Referencia y Estándares Técnicos (ADRs)

- **Código**: TI-EST-001
- **Versión**: 2.7 | **Fecha**: Febrero 2026
- **Propietario**: CTO — Andrés Flores Castillo
- **Clasificación**: CONFIDENCIAL — Uso interno técnico

### Secciones
1. Stack tecnológico aprobado: lenguajes (Python, Java, TypeScript, .NET), frameworks, bases de datos, cloud providers (AWS principal, Azure secundario, GCP excepcional).
2. Catálogo de ADRs vigentes (15 decisiones documentadas) — ej. "ADR-007: Adopción de event-driven con Kafka para integraciones bancarias".
3. Patrones obligatorios: autenticación (OAuth 2.0 + OIDC), logging estructurado (JSON), observabilidad (OpenTelemetry).
4. Estándares de seguridad de código: OWASP ASVS Nivel 2 mínimo, SAST en CI, secrets en Vault.
5. Política de dependencias open source: solo licencias permisivas (MIT, Apache 2.0, BSD), prohibido GPL en código entregable.
6. Arquitecturas de referencia por dominio: core banking, e-commerce retail, HIS hospitalario.

---

## D20 — Catálogo de Post-Mortems y Lessons Learned

- **Código**: TI-CONOC-001
- **Versión**: 2.4 | **Fecha**: Marzo 2026
- **Propietario**: CTO + PMO
- **Clasificación**: CONFIDENCIAL — Acceso a equipo técnico y gerentes de proyecto

### Secciones
1. Plantilla estándar de post-mortem (formato blameless).
2. Catálogo de 8 incidentes mayores 2023–2025 con: cliente afectado, severidad, duración, root cause, acciones correctivas.
3. Lessons learned categorizadas: técnicas (40%), gestión (35%), comerciales (25%).
4. Métricas agregadas: MTTR promedio por severidad, % de causas raíz repetidas, costo estimado de incidentes.
5. Top 5 causas raíz recurrentes y planes de mitigación estructurales.
6. Política de blamelessness y confidencialidad de post-mortems.

---

## D21 — Runbook de Delivery / SDLC Interno

- **Código**: TI-PROC-002
- **Versión**: 4.0 | **Fecha**: Enero 2026
- **Propietario**: CTO + PMO
- **Clasificación**: USO INTERNO

### Secciones
1. Fases del ciclo de delivery: Discovery (2–4 sem) → Design (2–6 sem) → Build (iterativo) → Test → Deploy → Hypercare (4 sem).
2. Quality gates por fase con criterios de salida medibles.
3. Definition of Done a tres niveles: historia, sprint, release.
4. Artefactos obligatorios por fase (visión, ADRs, plan de pruebas, runbook operativo, manual de usuario).
5. Ceremonias Agile estandarizadas: cadencias, duraciones, asistentes obligatorios.
6. Matriz RACI por entregable y rol.
7. Política de hypercare y handoff a soporte (KT obligatorio, 2 semanas mínimo).

---

## D22 — Gestión de Incidentes con Cliente y Cumplimiento de SLA

- **Código**: COMERCIAL-PROC-002
- **Versión**: 3.3 | **Fecha**: Febrero 2026
- **Propietario**: Gerencia Comercial + CTO
- **Clasificación**: CONFIDENCIAL — Uso interno comercial y técnico

### Secciones
1. Clasificación de severidad P1–P4 desde la perspectiva del cliente (distinto del D10, que es operación interna de TI).
2. Tiempos contractuales de respuesta y resolución: P1 → respuesta 15 min / resolución 4 h; P4 → 24 h / 5 días hábiles.
3. Penalidades por incumplimiento de SLA por cliente (referencia cruzada a D18).
4. Procedimiento de escalamiento con RACI: nivel 1 soporte → nivel 2 ingeniería → nivel 3 arquitecto → gerencia.
5. Plantillas de comunicación al cliente (acuse, actualización, RFO, cierre).
6. Post-mortem obligatorio en P1 y P2 (referencia a D20), entregable en 5 días hábiles.
7. Criterios de activación de war room y composición del equipo.

---

## D23 — Política de Uso de IA, LLMs y Datos Confidenciales

- **Código**: TI-POL-002
- **Versión**: 1.4 | **Fecha**: Abril 2026
- **Propietario**: CISO — Diana Reyes Castañeda + DPO — Mónica Salinas Bustamante
- **Clasificación**: USO INTERNO — Lectura obligatoria para todo el personal

### Secciones
1. Niveles de clasificación de datos: Público, Interno, Confidencial, Restringido (con ejemplos por tipo).
2. Matriz de uso permitido por nivel × herramienta: qué se puede subir a ChatGPT, Claude, Gemini, Copilot, herramientas internas.
3. Casos de uso aprobados de IA generativa: generación de boilerplate, redacción de comunicaciones internas, traducción, búsqueda semántica interna.
4. Casos prohibidos: subir código de clientes a LLMs públicos, ingresar datos personales identificables, compartir contratos o propuestas confidenciales.
5. Proceso de aprobación previa para nuevas herramientas con IA embebida (Notion AI, Granola, Cursor, etc.).
6. Auditoría: logging obligatorio de uso de IA corporativa, revisión trimestral por CISO.
7. Sanciones por incumplimiento (referencia a D06 Código de Conducta).

---

## Resumen de incorporación al pipeline

- **Generación**: replicar el patrón de `generate_docs_2.py`. Cada doc apunta a 5–7 páginas, mismo estilo formal.
- **Indexado**: agregar D16–D23 al pipeline RAG existente sin cambios de código (el loader ya levanta toda la carpeta).
- **Ground truth**: extender `nexus_ground_truth.json` con los nuevos objetos (`commercial_policies`, `technical_standards`, `ai_data_policy`). Ver archivo `nexus_ground_truth_tier3.json`.
- **Q&A pairs**: 40 nuevas preguntas (5 por doc), mismo formato RIKER. Ver `nexus_qa_pairs_tier3.json`.

## Para el paper

Los 8 nuevos docs habilitan el ablation por **tier de sensibilidad**:

| Tier | Docs | Hipótesis |
|---|---|---|
| Tier-1 (employee-facing) | D01–D08, D15 | RAG ≈ Fine-tune. Vocabulario genérico. |
| Tier-2 (operacional interno) | D09–D14 | RAG > Fine-tune. Datos cambiantes. |
| Tier-3 (estratégico confidencial) | D16–D23 | **Fine-tune + RAG > RAG solo**. Vocabulario propio, razonamiento de dominio, formato estructurado. |

Esta estratificación es la contribución metodológica diferencial del paper.
