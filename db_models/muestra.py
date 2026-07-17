from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Muestra(BaseModel):
    id: str = Field(alias="_id", default=None)
    clinica_id: str
    paciente_id: str
    tipo_muestra: str # Ej: "Sangre", "Saliva", "Tejido Tumoral"
    fecha_extraccion: datetime
    medico_solicitante: str
    estado: str = "Recolectada" # Recolectada, En Tránsito, Procesada, Analizada, Descartada
    temperatura_almacenamiento: Optional[float] = None
    notas: Optional[str] = None
    
    class Config:
        populate_by_name = True
