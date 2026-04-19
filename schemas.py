from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class ProyectoInfo(BaseModel):
    nombre: str
    marco_trabajo: str

class ResumenEjecutivo(BaseModel):
    interpretacion_tablero: str
    estado_proyecto: Literal[
        "sano",
        "ajustado",
        "en_riesgo",
        "critico",
        "sin_datos_suficientes",
    ]
    justificacion_estado: str

class KPIsInfo(BaseModel):
    cantidad_kpis: int
    kpis_criticos: List[str]

class RiesgosYOportunidades(BaseModel):
    riesgos: List[str]
    oportunidades: List[str]

class AccionesRecomendadas(BaseModel):
    equipo: List[str]
    sponsor: List[str]
    pmo: List[str]

class AnalisisPM(BaseModel):
    proyecto: ProyectoInfo
    resumen_ejecutivo: ResumenEjecutivo
    kpis: KPIsInfo
    riesgos_y_oportunidades: RiesgosYOportunidades
    acciones_recomendadas: AccionesRecomendadas
    version_modelo: Optional[str] = "vision-v2-2026"

class AnalisisResumen(BaseModel):
    id: int
    filename: str
    creado_en: datetime

    class Config:
        from_attributes = True

class AnalisisDetalle(BaseModel):
    id: int
    filename: str
    descripcion: str
    analisis_pm: AnalisisPM
    creado_en: datetime

    class Config:
        from_attributes = True

class VisionResponse(BaseModel):
    es_dashboard: bool
    motivo: str
    analisis_pm: Optional[AnalisisPM] = None