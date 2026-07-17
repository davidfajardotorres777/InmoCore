from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Alerta(BaseModel):
    id: str = Field(alias="_id", default=None)
    agencia_id: str
    tipo_alerta: str # Ej: "Temperatura Fuera de Rango", "Muestra Vencida"
    mensaje: str
    entidad_referencia_id: str # Puede ser el id de una muestra o un analisis
    resuelta: bool = False
    fecha_alerta: datetime = Field(default_factory=datetime.utcnow)
    fecha_resolucion: Optional[datetime] = None

    class Config:
        populate_by_name = True
