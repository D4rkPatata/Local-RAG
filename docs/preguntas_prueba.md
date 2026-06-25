# Guía de preguntas de prueba

Cómo probar: abre la app, **elige un rol** en el selector (arriba a la derecha) y
pega las preguntas. Cambiar de rol **reinicia** la conversación.

Roles y acceso: `colaborador_general` (Tier-1) · `mando_medio` (+Tier-2) ·
`comercial_senior` (+Tier-3 comercial) · `tecnico_senior` (+Tier-3 técnico) ·
`gerencia` (todo).

---

## 1. Tier-1 — todos los roles deben responder

| Pregunta | Respuesta esperada (cita) |
|---|---|
| ¿Cuántos días de vacaciones tengo al año? | 30 días [D03] |
| ¿Cuántos empleados tiene Nexus en total? | 148 empleados [D01] |
| ¿Quién es el CEO de Nexus y cuál es su anexo? | Ricardo Mendoza, anexo 101 [D15] |
| ¿De qué trata el plan de capacitación? | RRHH-POL-005, desarrollo de competencias [D07] |
| ¿Qué pasos tiene el onboarding de un nuevo colaborador? | proceso de inducción [D02] |

## 2. Tier-2 — solo `mando_medio` y superiores

| Pregunta | Esperado |
|---|---|
| ¿Cuál es la política de contraseñas de TI? | mín. 12 caracteres, expiran 90 días [D09] |
| ¿Cuánto es el viático diario en provincias? | S/120 por día [D13] |
| ¿Cuál es el tiempo de respuesta para un incidente P1 interno? | 15 min respuesta / 4 h resolución [D10] |

> Con `colaborador_general` estas deben dar **refusal** ("No tengo información…").

## 3. Tier-3 comercial — solo `comercial_senior` y `gerencia`

| Pregunta | Esperado |
|---|---|
| ¿Cuál es la tarifa hora de un Desarrollador Senior? | S/. 110 [D16] |
| ¿Cuál es el margen mínimo bajo Fixed Price? | 42% [D16] |
| ¿Cuál es el cliente con mayor contrato anual? | Banco Andino del Perú [D18] |
| ¿Qué nivel de aprobación necesita una propuesta de S/. 350,000? | CEO [D17] |

## 4. Tier-3 técnico — solo `tecnico_senior` y `gerencia`

| Pregunta | Esperado |
|---|---|
| ¿Cuál es el cloud provider primario aprobado? | AWS [D19] |
| ¿Qué licencias open source están prohibidas en código entregable? | GPL [D19] |
| ¿Cuál es el MTTR promedio de incidentes P1? | 3.2 horas [D20] |
| ¿Cuánto dura la fase de Hypercare? | 4 semanas [D21] |
| ¿Cuál es el proceso para aprobar una herramienta con IA? | ticket TI-IA al CISO [D23] |

---

## 5. Prueba de control de acceso (la demo clave)

Haz la **misma** pregunta cambiando de rol:

> **¿Cuál es la tarifa hora de un Desarrollador Senior?**

| Rol | Resultado esperado |
|---|---|
| `colaborador_general` | ❌ Refusal (no revela que existe) |
| `mando_medio` | ❌ Refusal |
| `tecnico_senior` | ❌ Refusal (es comercial, no técnico) |
| `comercial_senior` | ✅ "S/. 110 [D16]" |
| `gerencia` | ✅ "S/. 110 [D16]" |

Cruce de categorías Tier-3 (pregunta **técnica** a rol **comercial**):

> **¿Qué licencias open source están prohibidas?** con `comercial_senior` → ❌ Refusal
> (mismo rol, con `tecnico_senior` → ✅ "GPL [D19]")

---

## 6. Prueba de memoria de conversación (multi-turno)

Manda estas en secuencia, **sin cambiar de rol**. La 2ª/3ª pregunta solo tiene
sentido si el sistema recuerda la anterior.

**Secuencia A** (rol `colaborador_general`):
1. ¿De qué trata el plan de capacitación?
2. ¿Y cuál es su objetivo?
3. ¿Cuál es su presupuesto?

**Secuencia B** (rol `gerencia`):
1. ¿Cuál es el cliente con mayor contrato anual?
2. ¿Quién es su sponsor ejecutivo en Nexus?
3. ¿Cuándo vence ese contrato?

**Secuencia C** — seguimiento corto (rol `tecnico_senior`):
1. ¿Cuál es el cloud provider primario?
2. ¿Y el secundario?

> Sin memoria, "¿y el secundario?" no recuperaría nada útil. Con memoria, debe
> entender que hablas de cloud providers y responder "Azure [D19]".
