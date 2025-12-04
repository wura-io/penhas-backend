from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClienteBase(BaseModel):
    email: EmailStr
    nome_completo: str
    apelido: str
    status: Optional[str] = "setup"
    
class ClienteCreate(ClienteBase):
    password: str
    cpf: str # Will be hashed
    dt_nasc: datetime
    genero: str
    cep: str

class ClienteUpdate(BaseModel):
    nome_completo: Optional[str] = None
    apelido: Optional[str] = None
    minibio: Optional[str] = None

class ClienteInDBBase(ClienteBase):
    id: int
    created_on: datetime
    eh_admin: bool
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class Cliente(ClienteInDBBase):
    pass

