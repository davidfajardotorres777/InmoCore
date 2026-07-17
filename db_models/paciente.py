from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Paciente(BaseModel):
    id: str = Field(alias="_id", default=None)
    clinica_id: str
    dni: str
    nombre: str
    apellido: str
    fecha_nacimiento: datetime
    genero: str
    historial_medico: Optional[str] = None
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
