"""
SMS and communication logging models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class SentSmsLog(Base):
    """
    SMS sending log
    Port from SentSmsLog.pm
    """
    __tablename__ = "sent_sms_log"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=True, index=True)
    phone_number = Column(String(25), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False)  # sent, failed, etc.
    provider_response = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    cliente = relationship("Cliente")


class CpfErro(Base):
    """
    CPF validation errors
    Port from CpfErro.pm
    """
    __tablename__ = "cpf_erro"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cpf_hash = Column(String(200), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    remote_ip = Column(Text, nullable=True)

