const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageNumber, Header, Footer, TabStopType, TabStopPosition
} = require('/tmp/docx-env/node_modules/docx');
const fs = require('fs');

const BLUE_DARK  = "1F3864";
const BLUE_MID   = "2E75B6";
const BLUE_LIGHT = "D6E4F0";
const GRAY_LIGHT = "F2F2F2";
const GRAY_MID   = "BFBFBF";
const WHITE      = "FFFFFF";

const border = (color = GRAY_MID) => ({ style: BorderStyle.SINGLE, size: 1, color });
const noBorder = () => ({ style: BorderStyle.NONE, size: 0, color: "FFFFFF" });
const allBorders = (color) => ({ top: border(color), bottom: border(color), left: border(color), right: border(color) });
const noBorders = () => ({ top: noBorder(), bottom: noBorder(), left: noBorder(), right: noBorder() });

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 120 },
    children: [new TextRun({ text, bold: true, size: 36, color: BLUE_DARK, font: "Arial" })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 280, after: 100 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE_MID, space: 4 } },
    children: [new TextRun({ text, bold: true, size: 28, color: BLUE_MID, font: "Arial" })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, color: BLUE_DARK, font: "Arial" })] });
}
function body(text, opts = {}) {
  return new Paragraph({ spacing: { before: 80, after: 80 },
    children: [new TextRun({ text, size: 22, font: "Arial", ...opts })] });
}
function bullet(text, boldPart = null) {
  const runs = boldPart
    ? [new TextRun({ text: boldPart, bold: true, size: 22, font: "Arial" }), new TextRun({ text, size: 22, font: "Arial" })]
    : [new TextRun({ text, size: 22, font: "Arial" })];
  return new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { before: 60, after: 60 }, children: runs });
}
function callout(text) {
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], borders: noBorders(),
    rows: [new TableRow({ children: [new TableCell({
      shading: { fill: BLUE_LIGHT, type: ShadingType.CLEAR },
      borders: { ...noBorders(), left: { style: BorderStyle.SINGLE, size: 20, color: BLUE_MID } },
      margins: { top: 100, bottom: 100, left: 200, right: 200 },
      width: { size: 9360, type: WidthType.DXA },
      children: [new Paragraph({ children: [new TextRun({ text, size: 21, font: "Arial", italics: true })] })]
    })] })] });
}
function codeBlock(lines) {
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360], borders: noBorders(),
    rows: [new TableRow({ children: [new TableCell({
      shading: { fill: "1A2C4A", type: ShadingType.CLEAR }, borders: noBorders(),
      margins: { top: 120, bottom: 120, left: 200, right: 200 }, width: { size: 9360, type: WidthType.DXA },
      children: lines.map(({ text, color }) =>
        new Paragraph({ children: [new TextRun({ text, size: 18, font: "Courier New", color: color || "C8C8C8" })] }))
    })] })] });
}
function hdrCell(text, w, bg = BLUE_DARK) {
  return new TableCell({ shading: { fill: bg, type: ShadingType.CLEAR }, borders: noBorders(),
    margins: { top: 90, bottom: 90, left: 130, right: 130 }, width: { size: w, type: WidthType.DXA },
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, size: 20, font: "Arial", color: WHITE })] })] });
}
function dataCell(text, w, even = true, bold = false) {
  return new TableCell({ shading: { fill: even ? GRAY_LIGHT : WHITE, type: ShadingType.CLEAR }, borders: noBorders(),
    margins: { top: 75, bottom: 75, left: 130, right: 130 }, width: { size: w, type: WidthType.DXA },
    children: [new Paragraph({ children: [new TextRun({ text, size: 20, font: "Arial", bold })] })] });
}

// ───────── COVER ─────────
const cover = [
  new Paragraph({ spacing: { before: 1000 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "LOCAL RAG v2", bold: true, size: 72, color: BLUE_DARK, font: "Arial" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 140, after: 140 },
    children: [new TextRun({ text: "Installer Autónomo · Modelo GGUF Bundleado · Fine-Tuning por Nicho", size: 26, color: BLUE_MID, font: "Arial" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Plan Arquitectónico  —  Junio 2026", size: 22, color: "595959", font: "Arial" })] }),
  new Paragraph({ spacing: { before: 500 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: BLUE_MID } } }),
  new Paragraph({ children: [new TextRun({ break: 1 })] }),
];

// ───────── SEC 1: CONCEPTO ─────────
const sec1 = [
  h1("1. Cambio de Concepto"),
  body("El cambio fundamental es eliminar Ollama como proceso externo. El installer entregará tres piezas en un solo ejecutable:"),
  new Paragraph({ spacing: { before: 140 } }),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [3120, 3120, 3120], borders: noBorders(),
    rows: [new TableRow({ children:
      [["🔧 Motor de inferencia", "llama-cpp-python bundleado. Sin instalaciones separadas ni daemons."],
       ["🧠 Modelo cuantizado", "GGUF incluido (~4–5 GB). Offline desde el primer inicio."],
       ["💻 App completa", "FastAPI + ChromaDB + UI. Un solo .exe o carpeta dist."]
      ].map(([title, desc]) => new TableCell({
        shading: { fill: BLUE_LIGHT, type: ShadingType.CLEAR }, borders: allBorders(BLUE_LIGHT),
        margins: { top: 140, bottom: 140, left: 180, right: 180 }, width: { size: 3120, type: WidthType.DXA },
        children: [
          new Paragraph({ children: [new TextRun({ text: title, bold: true, size: 22, font: "Arial", color: BLUE_DARK })] }),
          new Paragraph({ spacing: { before: 60 }, children: [new TextRun({ text: desc, size: 20, font: "Arial" })] }),
        ]
      }))
    })]
  }),
  new Paragraph({ spacing: { before: 200 } }),
  h2("1.1 Por qué llama-cpp-python en lugar de Ollama"),
  body("Ollama es excelente para desarrollo, pero requiere instalación separada y levantar un daemon. Con llama-cpp-python:"),
  bullet("La inferencia ocurre dentro del mismo proceso Python — sin subprocesos externos."),
  bullet("El installer es completamente autónomo. El cliente descarga, instala, y ya funciona."),
  bullet("El modelo GGUF viaja junto con la app en el mismo ZIP o NSIS installer."),
  bullet("Expone una API compatible con OpenAI, por lo que los cambios al código existente son mínimos."),
  bullet("Soporte automático de GPU (CUDA / Metal / Vulkan) con n_gpu_layers=-1 sin cambio de código."),
  new Paragraph({ spacing: { before: 140 } }),
  callout("Cambio de mentalidad: Ollama es ideal para desarrollo local del programador. llama-cpp-python embebido es la arquitectura correcta para distribuir a clientes no-técnicos."),
  h2("1.2 Cambios al código"),
  body("Los únicos archivos que cambian son embedder.py y retriever.py. El resto de la app (parsers, vectorstore, UI, rutas FastAPI) se mantiene igual."),
  new Paragraph({ spacing: { before: 140 } }),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 4680], borders: noBorders(),
    rows: [
      new TableRow({ children: [
        new TableCell({ shading: { fill: BLUE_DARK, type: ShadingType.CLEAR }, borders: noBorders(), margins: { top: 90, bottom: 90, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Antes — Ollama HTTP", bold: true, size: 20, font: "Courier New", color: WHITE })] })] }),
        new TableCell({ shading: { fill: BLUE_MID, type: ShadingType.CLEAR }, borders: noBorders(), margins: { top: 90, bottom: 90, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Después — llama-cpp-python", bold: true, size: 20, font: "Courier New", color: WHITE })] })] }),
      ]}),
      new TableRow({ children: [
        new TableCell({ shading: { fill: "1A2C4A", type: ShadingType.CLEAR }, borders: noBorders(), margins: { top: 120, bottom: 120, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children:
          ['httpx.post(', '  ollama_url +', '  "/api/embeddings",', '  json={"model": ...,', '        "prompt": texto}', ')'].map(t => new Paragraph({ children: [new TextRun({ text: t, size: 18, font: "Courier New", color: "C8C8C8" })] }))
        }),
        new TableCell({ shading: { fill: "1A2C4A", type: ShadingType.CLEAR }, borders: noBorders(), margins: { top: 120, bottom: 120, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children:
          ['from llama_cpp import Llama', 'embed_model = Llama(', '  model_path="embed.gguf",', '  embedding=True)', '', 'embed_model.embed(texto)'].map(t => new Paragraph({ children: [new TextRun({ text: t, size: 18, font: "Courier New", color: t.startsWith('embed_model.embed') ? "A8D8A8" : "C8C8C8" })] }))
        }),
      ]}),
    ]
  }),
];

// ───────── SEC 2: MODELO ─────────
const sec2 = [
  new Paragraph({ spacing: { before: 240 } }),
  h1("2. Modelo Cuantizado Recomendado"),
  h2("2.1 Niveles de cuantización GGUF"),
  body("GGUF es el formato de distribución de llama.cpp: un solo archivo con pesos y metadatos. Los niveles más relevantes para un installer:"),
  new Paragraph({ spacing: { before: 140 } }),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [1800, 1800, 2360, 3400], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Nivel",1800), hdrCell("Tamaño (8B)",1800), hdrCell("Calidad",2360), hdrCell("Cuándo usarlo",3400)] }),
      ...([
        ["Q4_K_M","~4.5 GB","⭐⭐⭐⭐  Muy buena","Recomendado. Mejor balance calidad/tamaño para distribución."],
        ["Q5_K_M","~5.3 GB","⭐⭐⭐⭐⭐  Excelente","Si el cliente promedio tiene ≥16 GB de RAM."],
        ["Q6_K",  "~6.1 GB","Casi lossless","Hardware potente. Cerca de calidad FP16."],
        ["Q8_0",  "~8.6 GB","Referencia","Solo benchmarks. Demasiado grande para distribución."],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [1800,1800,2360,3400][j], i%2===0)) }))
    ]
  }),
  new Paragraph({ spacing: { before: 200 } }),
  h2("2.2 Modelo recomendado: Qwen3.5-8B"),
  body("El modelo base recomendado es Qwen3.5-8B Q4_K_M por cuatro razones clave:"),
  bullet("Soporte nativo de 201 idiomas — el mejor español entre modelos ≤8B del mercado en 2026."),
  bullet("Ventana de contexto de 256K tokens — ideal para RAG con documentos largos."),
  bullet("Fine-tuneable con Unsloth y exportable a GGUF directamente — flujo cerrado de entrenamiento → distribución."),
  bullet("Supera a Llama 3.1 8B y Phi-4 en benchmarks multilingües de razonamiento y comprensión."),
  new Paragraph({ spacing: { before: 120 } }),
  callout("Alternativa más pequeña: Qwen3-4B Q4_K_M (~2.3 GB). Reduce el installer a la mitad. Útil si el perfil del cliente es hardware de gama baja (8 GB RAM, sin GPU)."),
  new Paragraph({ spacing: { before: 160 } }),
  h2("2.3 Dos modelos GGUF separados"),
  body("Una decisión de arquitectura importante: usar GGUFs distintos para chat y para embeddings. Combinar ambas tareas en un solo modelo sacrifica calidad."),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2800, 1800, 4760], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Archivo",2800), hdrCell("Tamaño",1800), hdrCell("Función",4760)] }),
      ...([
        ["qwen3.5-8b-instruct-q4_k_m.gguf","~4.5 GB","Generación de respuestas (chat, RAG, streaming)"],
        ["nomic-embed-text-v1.5.Q8_0.gguf","~270 MB","Embeddings semánticos para ChromaDB"],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [2800,1800,4760][j], i%2===0)) }))
    ]
  }),
];

// ───────── SEC 3: PACKAGING ─────────
const sec3 = [
  new Paragraph({ spacing: { before: 240 } }),
  h1("3. Estrategia de Empaquetado"),
  h2("3.1 Estructura del dist/"),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [3400, 2000, 3960], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Componente",3400), hdrCell("Tamaño",2000), hdrCell("Notas",3960)] }),
      ...([
        ["localrag.exe",                      "~80 MB",   "Binario + Python + dependencias (PyInstaller)"],
        ["models/qwen3.5-8b-q4_k_m.gguf",    "~4.5 GB",  "Modelo de chat cuantizado"],
        ["models/nomic-embed-text.Q8_0.gguf", "~270 MB",  "Modelo de embeddings"],
        ["ui/static/",                         "< 1 MB",   "Frontend HTML/JS/CSS"],
        ["data/chroma_db/",                    "Variable", "Generado en primer uso (no se distribuye)"],
        ["TOTAL",                              "~5 GB",    "Distribuible por web, USB o CDN"],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [3400,2000,3960][j], i%2===0, j===0 && i===5)) }))
    ]
  }),
  new Paragraph({ spacing: { before: 200 } }),
  h2("3.2 Opción A (todo incluido) vs. Opción B (descarga guiada)"),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 4680], borders: noBorders(),
    rows: [
      new TableRow({ children: [
        new TableCell({ shading: { fill: BLUE_DARK, type: ShadingType.CLEAR }, borders: allBorders(BLUE_DARK), margins: { top: 100, bottom: 100, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Opción A — Todo incluido", bold: true, size: 22, font: "Arial", color: WHITE })] })] }),
        new TableCell({ shading: { fill: BLUE_MID, type: ShadingType.CLEAR }, borders: allBorders(BLUE_MID), margins: { top: 100, bottom: 100, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Opción B — App ligera + descarga ✅ Recomendada", bold: true, size: 22, font: "Arial", color: WHITE })] })] }),
      ]}),
      new TableRow({ children: [
        new TableCell({ shading: { fill: GRAY_LIGHT, type: ShadingType.CLEAR }, borders: allBorders(GRAY_MID), margins: { top: 100, bottom: 160, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children:
          ["✅ Funciona sin internet desde el día 1", "✅ Venta física en USB posible", "✅ Cero fricción de setup", "❌ Installer de ~5 GB", "❌ Difícil actualizar el modelo post-venta"].map(t => new Paragraph({ children: [new TextRun({ text: t, size: 20, font: "Arial" })] }))
        }),
        new TableCell({ shading: { fill: GRAY_LIGHT, type: ShadingType.CLEAR }, borders: allBorders(GRAY_MID), margins: { top: 100, bottom: 160, left: 160, right: 160 }, width: { size: 4680, type: WidthType.DXA }, children:
          ["✅ App < 100 MB, descarga rápida", "✅ Modelo actualizable sin reinstalar la app", "✅ Permite seleccionar modelo por nicho", "✅ Pantalla de descarga guiada y progresiva", "❌ Requiere ~5 GB de descarga en primer uso"].map(t => new Paragraph({ children: [new TextRun({ text: t, size: 20, font: "Arial" })] }))
        }),
      ]}),
    ]
  }),
  new Paragraph({ spacing: { before: 120 } }),
  body("Con Opción B, cada nicho tiene su propio GGUF fine-tuneado. El usuario descarga una vez el modelo de su sector y lo usa offline para siempre. Esto también permite vender 'módulos de nicho' como SKUs separados.", { bold: false }),
];

// ───────── SEC 4: NICHOS ─────────
function nichoTable(rows) {
  return new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2800, 6560], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Fuente de datos",2800), hdrCell("Qué extraer y cómo usarlo",6560)] }),
      ...rows.map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [2800,6560][j], i%2===0)) }))
    ]
  });
}

const sec4 = [
  new Paragraph({ spacing: { before: 240 } }),
  h1("4. Nichos para Fine-Tuning"),
  body("Un modelo fine-tuneado para un nicho específico supera en esa tarea a modelos 10x más grandes, con 10–20x menos costo de inferencia. Estos son los cinco nichos con mayor ROI en LATAM/España:"),
  new Paragraph({ spacing: { before: 200 } }),

  h2("4.1 🏦 Contabilidad y Fiscal  —  Nicho Prioritario"),
  body("Las firmas contables tienen decenas de documentos que sus empleados consultan diario: códigos tributarios, circulares del SAT/SUNAT/SII, formularios, y resoluciones. Hoy todo eso vive en archivadores o PDFs sin buscar."),
  h3("Problema concreto que resuelve"),
  bullet("¿Qué código de actividad económica le corresponde a una empresa de software SaaS?"),
  bullet("¿Cuál es el plazo para presentar el ISR mensual en Guatemala?"),
  bullet("¿El artículo 23 del Código Tributario aplica a esta situación de mi cliente?"),
  h3("Datos de entrenamiento"),
  nichoTable([
    ["Código Tributario nacional", "Artículos clave → pares Q&A sintéticos con GPT-4 (¿Cuándo aplica X? ¿Qué sanción tiene Y?)"],
    ["Circulares SAT/SUNAT/SII/AFIP", "Instrucciones procedimentales → formato de respuesta paso a paso"],
    ["Casos de clientes anonimizados", "Escenarios reales → ejemplos few-shot de razonamiento contable correcto"],
    ["Formularios + instructivos oficiales", "Preguntas de llenado → respuestas estructuradas con referencia a campo específico"],
    ["Resoluciones del tribunal fiscal", "Casos complejos → razonamiento jurídico-contable argumentado"],
  ]),
  new Paragraph({ spacing: { before: 140 } }),
  callout("Dataset mínimo viable: 800 pares Q&A curados. Costo estimado de generación GPT-4: ~$40 USD. Fine-tune Colab Pro+: ~$10 USD. ROI potencial: licencias por $30–80 USD/mes por firma contable."),

  new Paragraph({ spacing: { before: 200 } }),
  h2("4.2 ⚖️ Legal y Contratos"),
  body("Despachos de abogados y áreas legales corporativas pasan horas revisando si un contrato tiene cierta cláusula, buscando el artículo aplicable, o verificando consistencia entre documentos. Este trabajo es perfectamente paralelizable con RAG."),
  h3("Problema concreto"),
  bullet("¿Este contrato de arrendamiento incluye cláusula de indexación por inflación?"),
  bullet("¿Qué artículo del Código de Comercio regula la resolución de contratos por incumplimiento?"),
  bullet("¿Qué jurisprudencia existe sobre el plazo de prescripción en contratos de obra?"),
  h3("Datos de entrenamiento"),
  nichoTable([
    ["Código Civil + Código Comercio", "Artículos → Q&A de interpretación en lenguaje natural"],
    ["Contratos tipo públicos (arrendamiento, servicios, obra)", "Cláusulas → clasificación por tipo + redacción estándar sugerida"],
    ["Jurisprudencia (sentencias públicas)", "Razonamiento judicial → ejemplos de análisis legal estructurado"],
    ["Dataset EURLEX-ES / MIPEX", "Normativa europea en español → contexto legal amplio"],
    ["Contratos del propio despacho (anonimizados)", "El dataset más valioso — vocabulario y formato propios del cliente"],
  ]),

  new Paragraph({ spacing: { before: 200 } }),
  h2("4.3 🏥 Salud y Clínicas"),
  body("Clínicas privadas y laboratorios tienen protocolos, guías clínicas y formularios que el personal necesita consultar en tiempo real. Hoy viven en archivadores físicos o Word sin indexar."),
  h3("Problema concreto"),
  bullet("¿Cuál es el protocolo de antisepsia para una curación de herida de tercer grado?"),
  bullet("¿Qué contraindicaciones tiene el Metformín en pacientes con insuficiencia renal?"),
  bullet("¿Qué formulario se usa para solicitar estudios de imagen en el seguro X?"),
  h3("Datos de entrenamiento"),
  nichoTable([
    ["Guías de Práctica Clínica (GPC) del Ministerio", "Protocolos → instrucciones paso a paso con criterios de inclusión/exclusión"],
    ["Vademécum farmacológico", "Fármacos → uso, dosis, contraindicaciones, interacciones"],
    ["Protocolos internos de la clínica (anonimizados)", "Flujos internos → respuestas con tono y formato de la institución"],
    ["Formularios del seguro", "Preguntas de llenado → instrucciones de diligenciamiento por campo"],
  ]),
  new Paragraph({ spacing: { before: 120 } }),
  callout("IMPORTANTE: el fine-tune debe incluir ejemplos donde el modelo responde 'Esta pregunta requiere criterio médico. Consulta al profesional de salud.' Comportamiento conservador deliberado para preguntas fuera del alcance del protocolo."),

  new Paragraph({ spacing: { before: 200 } }),
  h2("4.4 🏢 Recursos Humanos y Compliance"),
  body("Empresas con 50–500 empleados tienen manuales de RRHH, reglamentos internos y normativas laborales que nadie lee hasta que hay un problema. Preguntas simples saturan al departamento de RRHH todos los días."),
  h3("Problema concreto"),
  bullet("¿Cuántos días de vacaciones me corresponden en mi quinto año de trabajo?"),
  bullet("¿Cuál es el procedimiento de baja por enfermedad según nuestro reglamento?"),
  bullet("¿La empresa está obligada a tener un comité de seguridad e higiene con este número de empleados?"),
  h3("Datos de entrenamiento"),
  nichoTable([
    ["Ley Federal del Trabajo / Estatuto de los Trabajadores", "Artículos clave → Q&A en lenguaje cotidiano (no legal)"],
    ["Convenios colectivos sectoriales (públicos)", "Cláusulas → interpretación aplicada al caso concreto"],
    ["Manual de RRHH de la empresa", "Políticas internas → respuestas que reflejan el tono corporativo del cliente"],
    ["Tickets históricos del departamento de RRHH", "El dataset de oro — preguntas reales + respuestas expertas ya validadas"],
  ]),

  new Paragraph({ spacing: { before: 200 } }),
  h2("4.5 🏗️ Construcción e Ingeniería"),
  body("Empresas constructoras, ingenieros y arquitectos trabajan con normas técnicas, pliegos de condiciones y especificaciones de materiales que son densos, muy específicos, y cambian por región."),
  h3("Problema concreto"),
  bullet("¿Qué resistencia mínima de concreto exige la NOM-006 para columnas de edificios de más de 4 pisos?"),
  bullet("¿Qué dice el pliego de condiciones del contrato sobre penalidades por atraso en obra?"),
  bullet("¿Cuál es el precio unitario de referencia para excavación en roca en la zona metropolitana?"),
  h3("Datos de entrenamiento"),
  nichoTable([
    ["Normas técnicas nacionales (NOM, NEC, NSR)", "Artículos + tablas → Q&A técnico con números y unidades exactos"],
    ["Pliegos de condiciones tipo de obra pública", "Cláusulas → interpretación contractual y consecuencias"],
    ["Especificaciones técnicas de fabricantes", "Instalación, compatibilidad, límites → instrucciones de aplicación"],
    ["Precios unitarios de referencia por región", "Partidas → estimaciones con desglose de materiales y mano de obra"],
  ]),
];

// ───────── SEC 5: FINE-TUNING TÉCNICO ─────────
const sec5 = [
  new Paragraph({ spacing: { before: 240 } }),
  h1("5. Hoja de Ruta Técnica de Fine-Tuning"),
  h2("5.1 Stack: QLoRA + Unsloth"),
  body("Para modelos ≤8B en 2026, el estándar es QLoRA con Unsloth. Es 2x más rápido que HuggingFace nativo y usa 60% menos VRAM. Para Qwen3.5-8B, una RTX 4090 o Google Colab Pro+ es suficiente."),
  new Paragraph({ spacing: { before: 140 } }),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2200, 7160], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Paso",2200), hdrCell("Detalle",7160)] }),
      ...([
        ["1. Recolectar datos", "Documentos del nicho (PDFs, DOCX, Excel). Mínimo recomendado: 500–1,000 pares Q&A de alta calidad. Calidad > cantidad."],
        ["2. Dataset sintético", "Usar GPT-4 para generar pares {instrucción, respuesta} desde los documentos. Herramienta: LlamaFactory o script propio. Costo: ~$40–80 USD por 1,000 pares."],
        ["3. Curar y filtrar", "Revisar 10–20% del dataset manualmente. Eliminar respuestas vagas, incorrectas o fuera de dominio. Este paso es el que más impacta en la calidad final."],
        ["4. Fine-tune con Unsloth", "Colab Pro+ (~$10/mes). 1,000 pasos ≈ 2–4 horas para 8B. Salida: adaptadores LoRA (.safetensors). Código disponible en unsloth.ai/docs."],
        ["5. Merge y export GGUF", "python merge_lora.py + llama.cpp convert_hf_to_gguf.py → cuantizar con quantize.exe -q q4_k_m. Este GGUF es el que se bundlea en el installer del nicho."],
        ["6. Evaluar", "50 preguntas del nicho. Comparar respuestas vs. modelo base. Métricas: precisión factual, tono, formato de respuesta, manejo de preguntas fuera de dominio."],
        ["7. Iterar", "Segunda ronda con los casos donde falló. 2–3 rondas suelen alcanzar el nivel de calidad de producción."],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [2200,7160][j], i%2===0)) }))
    ]
  }),

  new Paragraph({ spacing: { before: 200 } }),
  h2("5.2 Formato del dataset"),
  body("El formato más efectivo para Qwen3.5 es ChatML. Cada ejemplo tiene tres roles:"),
  new Paragraph({ spacing: { before: 140 } }),
  codeBlock([
    { text: '{"messages": [', color: "A8D8A8" },
    { text: '  {"role": "system",', color: "C8C8C8" },
    { text: '   "content": "Eres un asistente contable experto en legislación fiscal de México. Respondes con precisión, citas artículos cuando aplica, y dices claramente cuando la pregunta requiere criterio profesional."},', color: "FFD700" },
    { text: '  {"role": "user",', color: "C8C8C8" },
    { text: '   "content": "¿Cuál es la tasa de ISR para una persona física con actividad empresarial con ingresos de $500,000 MXN anuales?"},', color: "87CEEB" },
    { text: '  {"role": "assistant",', color: "C8C8C8" },
    { text: '   "content": "Según el Artículo 152 de la LISR, una persona física con actividad empresarial que perciba $500,000 MXN aplica la tasa del 30%. El cálculo base es: [detalle paso a paso]..."}', color: "FFA07A" },
    { text: ']}', color: "A8D8A8" },
  ]),

  new Paragraph({ spacing: { before: 200 } }),
  h2("5.3 Costo estimado por nicho"),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2800, 2000, 1960, 1400, 1200], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Nicho",2800), hdrCell("Pares Q&A",2000), hdrCell("Costo GPT-4",1960), hdrCell("Colab",1400), hdrCell("Total",1200)] }),
      ...([
        ["Contabilidad / Fiscal", "800–1,200", "~$50–80", "~$10", "~$70"],
        ["Legal / Contratos",     "600–1,000", "~$40–70", "~$10", "~$60"],
        ["Salud / Clínicas",      "500–800",   "~$35–60", "~$10", "~$55"],
        ["RRHH / Compliance",     "400–700",   "~$30–50", "~$10", "~$50"],
        ["Construcción",          "500–900",   "~$40–70", "~$10", "~$60"],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [2800,2000,1960,1400,1200][j], i%2===0, j===4)) }))
    ]
  }),
  new Paragraph({ spacing: { before: 120 } }),
  callout("El dataset sintético es el costo principal. Genera los pares de forma inteligente: primero extrae fragmentos clave de los documentos, luego pide a GPT-4 3 preguntas + respuestas por fragmento. 300 fragmentos × 3 = 900 pares por ~$60 USD."),
];

// ───────── SEC 6: ROADMAP + RESUMEN ─────────
const sec6 = [
  new Paragraph({ spacing: { before: 240 } }),
  h1("6. Roadmap de Implementación"),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [1200, 1800, 6360], borders: noBorders(),
    rows: [
      new TableRow({ children: [hdrCell("Fase",1200), hdrCell("Tiempo",1800), hdrCell("Tareas",6360)] }),
      ...([
        ["1","1–2 sem.", "Reemplazar Ollama por llama-cpp-python. Actualizar embedder.py, retriever.py, config/__init__.py. Eliminar startup wizard de Ollama."],
        ["2","1 sem.",   "Bajar Qwen3.5-8B Q4_K_M + nomic-embed-text GGUF. Validar calidad de respuestas, velocidad y uso de RAM en hardware de referencia (8 GB / 16 GB, sin GPU)."],
        ["3","1 sem.",   "Actualizar PyInstaller .spec para incluir llama-cpp-python + GGUFs. Probar build completo en Windows. Implementar pantalla de descarga del modelo (Opción B)."],
        ["4","2–4 sem.", "Fine-tuning primer nicho (Contabilidad). Recolectar docs → generar dataset → QLoRA con Unsloth → exportar GGUF cuantizado."],
        ["5","1 sem.",   "Evaluar modelo fine-tuneado vs. base. Ajustar system prompt. Beta con 2–3 firmas contables reales. Recoger feedback."],
        ["6","Continuo", "Replicar el pipeline para 2–4 nichos adicionales. Cada nicho = GGUF propio descargable desde la app → modelo de distribución por módulos."],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => dataCell(cell, [1200,1800,6360][j], i%2===0)) }))
    ]
  }),

  new Paragraph({ spacing: { before: 240 } }),
  h1("7. Resumen Ejecutivo"),
  new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [3000, 6360], borders: noBorders(),
    rows: [
      ...([
        ["Motor de inferencia", "llama-cpp-python (reemplaza Ollama — sin daemon externo)"],
        ["Modelo de chat", "Qwen3.5-8B Q4_K_M — mejor español/multilingüe ≤8B en 2026 (~4.5 GB)"],
        ["Modelo de embeddings", "nomic-embed-text-v1.5 Q8_0 — 270 MB, alta precisión semántica"],
        ["Tamaño del installer", "~80 MB app + descarga guiada de ~5 GB del modelo (Opción B recomendada)"],
        ["Técnica de fine-tuning", "QLoRA con Unsloth → merge → exportar a GGUF Q4_K_M"],
        ["Nicho prioritario", "Contabilidad/Fiscal — mayor volumen de clientes y densidad documental en LATAM"],
        ["Nichos secundarios", "Legal, Salud, RRHH/Compliance, Construcción"],
        ["Costo por nicho", "~$50–80 USD (datos sintéticos) + ~$10 USD (cómputo) = ~$60–90 USD total"],
        ["Tiempo por nicho", "1–2 semanas desde recolección hasta GGUF listo para distribución"],
        ["Propuesta de valor", "App local sin suscripciones ni internet, fine-tuneada para el sector, instalable en 5 minutos"],
      ]).map((row, i) => new TableRow({ children: row.map((cell, j) => new TableCell({
        shading: { fill: j === 0 ? BLUE_DARK : (i%2===0 ? BLUE_LIGHT : WHITE), type: ShadingType.CLEAR },
        borders: noBorders(), margins: { top: 90, bottom: 90, left: 140, right: 140 },
        width: { size: [3000,6360][j], type: WidthType.DXA },
        children: [new Paragraph({ children: [new TextRun({ text: cell, size: 21, font: "Arial", bold: j===0, color: j===0 ? WHITE : "000000" })] })]
      })) }))
    ]
  }),
];

// ───────── BUILD ─────────
const doc = new Document({
  numbering: {
    config: [{
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 600, hanging: 300 } } } }]
    }]
  },
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: BLUE_DARK },
        paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: BLUE_MID },
        paragraph: { spacing: { before: 280, after: 100 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: BLUE_DARK },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1260, bottom: 1440, left: 1260 } }
    },
    headers: { default: new Header({ children: [new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BLUE_MID, space: 4 } },
      children: [new TextRun({ text: "LOCAL RAG v2  —  Plan Arquitectónico", size: 18, font: "Arial", color: "595959" })]
    })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      border: { top: { style: BorderStyle.SINGLE, size: 4, color: BLUE_MID, space: 4 } },
      tabStops: [{ type: TabStopType.RIGHT, position: 9360 }],
      children: [
        new TextRun({ text: "Confidencial  •  Junio 2026", size: 18, font: "Arial", color: "595959" }),
        new TextRun({ children: ["\t", "Página ", PageNumber.CURRENT, " de ", PageNumber.TOTAL_PAGES], size: 18, font: "Arial", color: "595959" }),
      ]
    })] }) },
    children: [...cover, ...sec1, ...sec2, ...sec3, ...sec4, ...sec5, ...sec6]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/sessions/compassionate-ecstatic-cray/mnt/14. Local-RAG/plan_localrag_v2.docx', buf);
  console.log('DONE');
}).catch(e => { console.error(e); process.exit(1); });
