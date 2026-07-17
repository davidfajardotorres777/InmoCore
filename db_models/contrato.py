from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Contrato(BaseModel):
    id: str = Field(alias="_id", default=None)
    agencia_id: str
    propiedad_id: str
    cliente_id: str
    tipo_contrato: str
    monto_total: float
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    archivo_path: Optional[str] = None # MinIO Path
    
    class Config:
        populate_by_name = True
