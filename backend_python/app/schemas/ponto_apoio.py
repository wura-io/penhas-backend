from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PontoApoioBase(BaseModel):
    nome: str
    natureza: str
    categoria: int
    municipio: str
    uf: str

class PontoApoioCreate(PontoApoioBase):
    pass

class PontoApoio(PontoApoioBase):
    id: int
    created_on: datetime
    status: str
    descricao: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    avaliacao: float

    class Config:
        from_attributes = True

