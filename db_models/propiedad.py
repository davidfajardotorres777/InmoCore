from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Propiedad(BaseModel):
    id: str = Field(alias="_id", default=None)
    agencia_id: str
    titulo: str
    descripcion: str
    tipo: str # Casa, Departamento, Terreno
    operacion: str # Venta, Alquiler
    precio_usd: float
    superficie_m2: float
    habitaciones: int
    ubicacion: Optional[dict] = None # GeoJSON Point
    fotos_paths: Optional[List[str]] = [] # URLs/Paths in MinIO
    fecha_publicacion: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
