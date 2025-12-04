from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GuardiaoBase(BaseModel):
    nome: str
    celular_e164: str

class GuardiaoCreate(GuardiaoBase):
    pass

class Guardiao(GuardiaoBase):
    id: int
    status: str
    created_at: datetime
    expires_at: datetime
    celular_formatted_as_national: str

    class Config:
        from_attributes = True

