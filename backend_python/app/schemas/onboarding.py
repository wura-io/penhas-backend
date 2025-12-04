from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class SignupRequest(BaseModel):
    nome_completo: str
    dt_nasc: date
    cpf: str
    cep: str
    app_version: str
    email: Optional[EmailStr] = None
    genero: Optional[str] = None
    nome_social: Optional[str] = None
    raca: Optional[str] = None
    apelido: Optional[str] = None
    senha: Optional[str] = None
    dry: int = 0

class PasswordResetRequest(BaseModel):
    email: EmailStr
    app_version: str

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    token: str
    senha: Optional[str] = None
    dry: int = 0

