# Standard lib
import os
import base64
from typing import Optional, List

# Third party
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from openai import AzureOpenAI
from dotenv import load_dotenv

# Local
from app.utils.validators import parse_json_safe
from app.utils.kpiglobalmap import KPI_LIST
from app.features import _classify_approach
from database import (
    ENABLE_DB,
    init_db,
    get_db_optional,
    AnalisisDashboard,
    VisionRequestsLog,
    VisionEventType,
)
from schemas import AnalisisResumen, AnalisisDetalle, AnalisisPM

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY      = os.getenv("AZURE_OPENAI_KEY")
DEPLOYMENT_NAME       = os.getenv("DEPLOYMENT_NAME")

MAX_LIMIT = 100

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-08-01-preview"
)

app = FastAPI(
    title="INFY VISION API",
    description="STANDARD (agnóstico universal) + ELITE (suitability agnóstico real)",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar tablas al arrancar
@app.on_event("startup")
def startup():
    init_db()


# =============================================================================
# KPI VOCABULARY
# =============================================================================
def _get_kpi_vocabulary() -> str:
    return ", ".join(KPI_LIST[:80])


# =============================================================================
# HELPERS
# =============================================================================
def _safe(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except Exception:
        return default

def _flatten_kpis(kpis: dict) -> dict:
    """Garantiza que kpis_detectados sea siempre { str: number }"""
    result = {}
    for k, v in kpis.items():
        if isinstance(v, (int, float)):
            result[k] = v
        elif isinstance(v, dict):
            for subk, subv in v.items():
                if isinstance(subv, (int, float)):
                    result[f"{k}_{subk}"] = subv
                    break
        elif isinstance(v, str):
            try:
                result[k] = float(v.replace('%', '').replace(',', ''))
            except ValueError:
                pass
    return result


# =============================================================================
# MOTOR ÚNICO — Una sola llamada
# =============================================================================
def analizar_todo(imagen_bytes: bytes, kpi_vocab_str: str) -> dict:
    imagen_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

    completion = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
        messages=[
            {
                "role": "system",
                "content": f"""
Eres Brian, un analista experto universal con dominio en gestión de proyectos,
finanzas, ingeniería, medicina, derecho, periodismo, y cualquier otra
disciplina. Tienes capacidad de leer e interpretar cualquier documento,
imagen o tablero que caiga en tus manos.

══════════════════════════════════════════════════════════════
FASE 1 — DESCRIPCIÓN HORIZONTAL
══════════════════════════════════════════════════════════════
Describe todo lo que ves en la imagen de izquierda a derecha, de arriba a abajo.
Si hay una tabla: fila por fila indicar los datos de cada KPI. Si hay un gráfico: sección por sección.
Sé exhaustivo y preciso. Si una columna repite el mismo dato, expresarlo sin redundar.

La estructura JSON para tablas DEBE ser un array de objetos, uno por fila:
[
  {{
    "proyecto": "<valor>",
    "marco": "<valor>",
    "dimension": "<valor>",
    "kpi": "<valor>",
    "valor": <numero>,
    "unidad": "<valor>",
    "umbral_verde": <numero o null>,
    "umbral_amarillo": <numero o null>,
    "estado": "<valor>",
    "que_mide": "<valor>"
  }}
]
PROHIBIDO usar arrays paralelos como "kpi": ["SV","SPI"...], "valor": [-8, 0.96...].
Cada fila de la tabla = un objeto JSON independiente.

Si hay una fila o sección con índices de suitability (Experience, Access, Buy-In, etc.),
inclúyela como objeto separado dentro de descripcion_horizontal:
{{
  "suitability_indexes": {{
    "experience": <numero o null>,
    "access": <numero o null>,
    "buy_in": <numero o null>,
    "trust": <numero o null>,
    "decision": <numero o null>,
    "delivery": <numero o null>,
    "criticality": <numero o null>,
    "changes": <numero o null>,
    "team_size": <numero o null>
  }}
}}


══════════════════════════════════════════════════════════════
FASE 2 — ANÁLISIS EXPERTO
══════════════════════════════════════════════════════════════
Entrega el análisis más valioso posible según el contexto del contenido.
KPIs, umbrales, estados, tendencias, riesgos, recomendaciones.
Si no hay KPIs, analiza lo que haya con la misma profundidad.

Si detectas índices de suitability (Experience, Access, Buy-In, Trust,
Decision, Delivery, Criticality, Changes, Team Size), recuerda por favor esta
premisa al opinar: IMPORTANTE: Indicar el valor de cada uno y el enfoque de gestión que toma:

- experience:   ALTO = (Predictivo, poca experiencia en ágil) / BAJO = (Ágil, más experiencia en entornos ágiles)
- access:       ALTO = (Predictivo, menos acceso a cliente) / BAJO = (ÁGIL, hay mayor acceso a cliente)
- trust:        BAJO = (Ágil, mayor confianza en el equipo) / ALTO = (Predictivo, falta de confianza en el equipo)
- decision:     BAJO = (Ágil, decisiones rápidas distribuidas) / ALTO = (jerárquico, más predictivo)
- buy_in:       ALTO = (Predictivo, poca aceptación de autonomía del team) / BAJO = (Ágil, aceptan autonomía del equipo)
- team_size:    BAJO = (Ágil; se maneja grupos pequeños) / ALTO = (Predictivo, generalmente grupos numerosos)
- changes:      BAJO = (Ágil; alta incertidumbre) / ALTO = (Predictivo, debido a pocos cambios)
- criticality:  ALTO = (Predictivo, riesgo alto) / BAJO = (Ágil; tolerante a error)
- delivery:     BAJO = (Ágil, prueba entrega incremental) / ALTO = (Predictivo, prefiere única entrega,)  

1. Indica el valor de índice y BASANDOTE UNICAMENTE EN EL NUMERO dices su
comentario correspondiente (el cual está en paréntesis). Nada más.

Los valores NO SON "buenos o malos", solo dí el número y ya sea bajo o alto dicho valor, brinda el comentario que toque.
Excepción; 
- Híbrido (si encuentras un punto medio)

══════════════════════════════════════════════════════════════
FASE 3 — EXTRACCIÓN RAW
══════════════════════════════════════════════════════════════
Si detectas índices de suitability en la imagen, extráelos TAL COMO
APARECEN — sin convertir, sin invertir. Solo el número visual.

CASO A — Valores en tabla o texto:
Lee el número directamente. No hay ambigüedad.

CASO B — Gráfico radial (spider/radar chart):
Ejecuta este protocolo eje por eje, SIN EXCEPCIÓN:

1. IDENTIFICA el nombre de cada eje en el borde exterior del radar.
   Los ejes típicos son: Experiencia/Experience, Acceso/Access,
   Aceptación/Buy-In, Confianza/Trust, Toma de decisiones/Decision,
   Entrega/Delivery, Criticidad/Criticality, Cambios/Changes,
   Tamaño del Equipo/Team Size.

2. Para CADA eje, sigue esta secuencia de razonamiento OBLIGATORIA:
   a) Traza mentalmente la línea desde el centro hacia el borde en ese eje.
   b) Localiza el vértice del polígono sobre ESE eje específico.
   c) Compara la distancia del vértice con los anillos numerados visibles.
      - Si el vértice toca el borde exterior → valor 10
      - Si está justo en el anillo 7 → valor 7
      - Si está entre anillo 6 y 7, más cerca del 7 → valor 6 o 7
      - Si está cerca del centro (anillo 1-2) → valor bajo
   d) Escribe el valor resultante. NO copies el valor de otro eje.

3. PROHIBIDO:
   - Asumir simetría (que todos los ejes tienen valores similares)
   - Promediar visualmente entre ejes
   - Inventar valores sin razonar eje por eje
   - Dar el mismo valor a múltiples ejes sin justificación visual

4. Si el radar está en escala de grises o baja resolución, usa el
   contraste del polígono vs los anillos de fondo para estimar.
   Es preferible un valor aproximado honesto que uno inventado.

5. Si hay NÚMEROS escritos en la tabla junto al radar, PRIORIZA
   esos números sobre la lectura visual del gráfico.

Si no hay suitability en la imagen, devuelve suitability_raw como objeto vacío {{}}.

══════════════════════════════════════════════════════════════
FASE 4 — KPIs Y FRAMEWORK
══════════════════════════════════════════════════════════════
Si detectas alguno de estos KPIs en la imagen, inclúyelo con su valor:
{kpi_vocab_str}

Detecta el framework si aparece (Scrum, Kanban, SAFe, PMBOK, Crystal, etc.)

IMPORTANTE: kpis_detectados debe contener MÁXIMO 8 KPIs.
Prioriza KPIs agregados/totales. NO incluyas KPIs por artículo individual.
Ejemplo correcto: "total_ingresos_real", "margen_bruto_promedio"
Ejemplo incorrecto: "margen_bruto_articulo_1", "margen_bruto_articulo_2"...

══════════════════════════════════════════════════════════════
RESPONDE SOLO EN JSON VÁLIDO:
{{
  "descripcion_horizontal": {{ ... }},
  "analisis_experto": {{ ... }},
  "suitability_raw": {{
    "experience":  <número tal como aparece en la imagen o null>,
    "access":      <número tal como aparece en la imagen o null>,
    "buy_in":      <número tal como aparece en la imagen o null>,
    "trust":       <número tal como aparece en la imagen o null>,
    "decision":    <número tal como aparece en la imagen o null>,
    "delivery":    <número tal como aparece en la imagen o null>,
    "criticality": <número tal como aparece en la imagen o null>,
    "changes":     <número tal como aparece en la imagen o null>,
    "team_size":   <número tal como aparece en la imagen o null>
  }},
  "framework_detectado": "<framework o null>",
  "kpis_detectados": {{ "<codigo_kpi>": <valor_numerico> }},
  "confianza_lectura": "<alta|media|baja>",
  "notas_lectura": "<observaciones si las hay>"
}}
No escribas texto fuera del JSON.
"""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analiza esta imagen."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{imagen_b64}"}
                    }
                ]
            }
        ],
        temperature=0.2,
        max_tokens=4000,
        response_format={"type": "json_object"}
    )

    return parse_json_safe(completion.choices[0].message.content)


# =============================================================================
# PIPELINE SUITABILITY — RAW → INFY
# =============================================================================
def _build_suitability_infy(raw: dict) -> dict:
    keys = ["experience", "access", "buy_in", "trust", "decision",
            "delivery", "criticality", "changes", "team_size"]
    return {k: raw.get(k) for k in keys}


# =============================================================================
# CLASSIFY
# =============================================================================
def clasificar_enfoque(suitability_infy: dict, framework: str | None) -> dict:
    return _classify_approach(
        framework   = framework or "Hybrid",
        experience  = _safe(suitability_infy.get("experience")),
        access      = _safe(suitability_infy.get("access")),
        delivery    = _safe(suitability_infy.get("delivery")),
        criticality = _safe(suitability_infy.get("criticality")),
        changes     = _safe(suitability_infy.get("changes")),
        buy_in      = _safe(suitability_infy.get("buy_in")),
        trust       = _safe(suitability_infy.get("trust")),
        decision    = _safe(suitability_infy.get("decision")),
        governance  = _safe(suitability_infy.get("governance")),
    )


def formatear_veredicto(classify: dict) -> str:
    approach = classify.get("approach_infy", "Hybrid")
    more     = classify.get("suitability_more_pred", False)
    less     = classify.get("suitability_less_pred", False)
    mismatch = classify.get("suitability_mismatch", False)

    if mismatch:
        return "⚠️ MISMATCH — Hay una desalineación fuerte entre el marco que usas y el contexto real del proyecto."
    elif more:
        return "🔒 Endurece el enfoque — El contexto de criticidad/governance exige moverse hacia Predictivo."
    elif less:
        return "🔓 Flexibiliza el enfoque — El nivel de cambio y acceso permite soltar control hacia Ágil."
    else:
        return f"✅ Marco y contexto alineados — Enfoque {approach} es consistente con tu realidad de proyecto."


# =============================================================================
# ENDPOINT 1 — STANDARD
# =============================================================================
@app.post("/vision-analysis", summary="INFY VISION STANDARD — Análisis agnóstico universal")
async def vision_analysis(file: UploadFile = File(...)):
    contenido  = await file.read()
    kpi_vocab  = _get_kpi_vocabulary()

    try:
        data = analizar_todo(contenido, kpi_vocab)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return jsonable_encoder({
        "mode":                   "STANDARD",
        "descripcion_horizontal": data.get("descripcion_horizontal", {}),
        "analisis_experto":       data.get("analisis_experto", {}),
    })


# =============================================================================
# ENDPOINT 2 — ELITE (con persistencia opcional en DB)
# =============================================================================
@app.post("/vision-analysis/elite", summary="INFY VISION ELITE — Suitability agnóstico")
async def vision_analysis_elite(
    file: UploadFile = File(...),
    db=Depends(get_db_optional)
):
    contenido = await file.read()
    kpi_vocab = _get_kpi_vocabulary()

    log_data = {
        "endpoint": "/vision-analysis/elite",
        "filename": file.filename,
        "input_metadata": {
            "size_bytes": len(contenido),
            "content_type": file.content_type,
        },
    }

    try:
        data = analizar_todo(contenido, kpi_vocab)
    except Exception as e:
        if ENABLE_DB and db:
            db.add(VisionRequestsLog(
                **log_data,
                event_type=VisionEventType.OPENAI_ERROR,
                error_detail=str(e),
            ))
            db.commit()
        raise HTTPException(status_code=500, detail=str(e))

    # Pipeline suitability: RAW → INFY
    suitability_raw  = data.get("suitability_raw", {})
    suitability_infy = _build_suitability_infy(suitability_raw)

    framework   = data.get("framework_detectado")
    kpis_vistos = _flatten_kpis(data.get("kpis_detectados", {}))
    confianza   = data.get("confianza_lectura", "media")
    notas       = data.get("notas_lectura", "")

    classify  = clasificar_enfoque(suitability_infy, framework)
    veredicto = formatear_veredicto(classify)

    analisis_id = None

    if ENABLE_DB and db:
        # Guardar análisis principal
        _ae = data.get("analisis_experto", {})
        _desc = (
            _ae.get("resumen") or _ae.get("conclusion") or
            _ae.get("sintesis") or str(_ae)[:300] or "Sin resumen"
        )
        registro = AnalisisDashboard(
            filename=file.filename,
            descripcion=_desc,
            analisis_pm=jsonable_encoder({
                "suitability_indexes": suitability_infy,
                "suitability_raw":     suitability_raw,
                "framework_detectado": framework,
                "kpis_detectados":     kpis_vistos,
                "veredicto":           veredicto,
                "approach_infy":       classify.get("approach_infy"),
                "confianza_lectura":   confianza,
                "notas_lectura":       notas,
                "descripcion_horizontal": data.get("descripcion_horizontal", {}),
                "analisis_experto":       data.get("analisis_experto", {}),
            })
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)
        analisis_id = registro.id

        # Log OK
        db.add(VisionRequestsLog(
            **log_data,
            event_type=VisionEventType.OK,
            analisis_id=analisis_id,
        ))
        db.commit()

    return jsonable_encoder({
        "id":   analisis_id,
        "mode": "ELITE",

        "standard": {
            "descripcion_horizontal": data.get("descripcion_horizontal", {}),
            "analisis_experto":       data.get("analisis_experto", {}),
        },

        "elite": {
            "approach_infy":         classify.get("approach_infy"),
            "framework_detectado":   framework,
            "suitability_indexes":   suitability_infy,
            "suitability_raw":       suitability_raw,
            "veredicto":             veredicto,
            "suitability_more_pred": classify.get("suitability_more_pred"),
            "suitability_less_pred": classify.get("suitability_less_pred"),
            "suitability_mismatch":  classify.get("suitability_mismatch"),
            "suitability_note":      classify.get("suitability_note"),
            "confianza_lectura":     confianza,
            "notas_lectura":         notas,
            "kpis_detectados":       kpis_vistos,
        },
    })


# =============================================================================
# ENDPOINT 3 — LISTAR HISTÓRICO
# =============================================================================
@app.get("/analisis", response_model=List[AnalisisResumen], summary="Histórico de análisis")
def list_analisis(skip: int = 0, limit: int = 20, db=Depends(get_db_optional)):
    if not ENABLE_DB or not db:
        raise HTTPException(status_code=503, detail="DB no disponible")
    safe_limit = min(limit, MAX_LIMIT)
    registros = (
        db.query(AnalisisDashboard)
        .order_by(AnalisisDashboard.id.desc())
        .offset(skip)
        .limit(safe_limit)
        .all()
    )
    return registros


# =============================================================================
# ENDPOINT 4 — DETALLE POR ID
# =============================================================================
@app.get("/analisis/{id}", response_model=AnalisisDetalle, summary="Detalle de análisis")
def get_analisis(id: int, db=Depends(get_db_optional)):
    if not ENABLE_DB or not db:
        raise HTTPException(status_code=503, detail="DB no disponible")
    registro = db.query(AnalisisDashboard).filter(AnalisisDashboard.id == id).first()
    if not registro:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")
    return registro


# =============================================================================
# ENDPOINT 5 — HEALTH
# =============================================================================
@app.get("/health", summary="Health check")
async def health():
    try:
        from app.features import PROJECT_KPI_MAPS
        kpi_total   = sum(len(v) for v in PROJECT_KPI_MAPS.values())
        features_ok = True
    except Exception:
        kpi_total   = 0
        features_ok = False

    return {
        "status":          "ok",
        "version":         "5.0.0",
        "db_enabled":      ENABLE_DB,
        "features_module": "ok" if features_ok else "error",
        "kpi_vocabulary":  f"{len(KPI_LIST)} KPIs disponibles",
        "endpoints": {
            "STANDARD":  "POST /vision-analysis",
            "ELITE":     "POST /vision-analysis/elite",
            "HISTORICO": "GET  /analisis",
            "DETALLE":   "GET  /analisis/{id}",
            "HEALTH":    "GET  /health",
        }
    }
