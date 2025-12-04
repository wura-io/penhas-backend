from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class ClientesResetPassword(Base):
    __tablename__ = "clientes_reset_password"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    token = Column(String(200), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    requested_by_remote_ip = Column(String(200), nullable=False)
    used_by_remote_ip = Column(String(200))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="clientes_reset_passwords")

class LoginLog(Base):
    __tablename__ = "login_log"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    remote_ip = Column(String(200), nullable=False)
    app_version = Column(String(200))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="login_logs")

class LoginErro(Base):
    __tablename__ = "login_erro"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=True)
    email = Column(String(200), nullable=True)
    remote_ip = Column(String(200), nullable=False)
    error_type = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="login_erros")

class CpfErro(Base):
    __tablename__ = "cpf_erro"

    id = Column(BigInteger, primary_key=True, index=True)
    cpf_hash = Column(String(200), nullable=False, index=True)
    error_message = Column(String(500), nullable=False)
    remote_ip = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class ClientesActiveSession(Base):
    __tablename__ = "clientes_active_sessions"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="clientes_active_sessions")

