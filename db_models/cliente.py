from pydantic import BaseModel, Field
from datetime import datetime

class Cliente(BaseModel):
    id: str = Field(alias="_id", default=None)
    agencia_id: str
    dni: str
    nombre: str
    apellido: str
    telefono: str
    email: str
    fecha_registro: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
