from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class Analisis(BaseModel):
    id: str = Field(alias="_id", default=None)
    clinica_id: str
    muestra_id: str
    tipo_analisis: str # Ej: "Secuenciación WGS", "PCR", "Panel Genético"
    fecha_analisis: datetime = Field(default_factory=datetime.utcnow)
    laboratorio_origen: str
    investigador_responsable: str
    resultados_crudos_path: Optional[str] = None # Path al S3/MinIO
    metricas_calidad: Dict[str, Any] = Field(default_factory=dict)
    hallazgos_clinicos: Optional[str] = None
    
    class Config:
        populate_by_name = True
