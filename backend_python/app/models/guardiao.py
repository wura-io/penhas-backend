from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class ClientesGuardio(Base):
    __tablename__ = "clientes_guardioes"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    celular_e164 = Column(String(25), nullable=False)
    nome = Column(String(200), nullable=False)
    token = Column(String(200), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime(timezone=True))
    accepted_meta = Column(Text, nullable=False, server_default=text("'{}'"))
    celular_formatted_as_national = Column(String(25), nullable=False)
    refused_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    estava_em_situacao_risco = Column(Boolean, nullable=False, default=False)

    cliente = relationship("Cliente") # back_populates can be added later

