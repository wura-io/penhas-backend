"""
Blocking and reporting models - Cliente blocking, timeline blocking, and reporting
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class ClienteBloqueio(Base):
    """
    User blocking - when one user blocks another
    Port from ClienteBloqueio.pm
    """
    __tablename__ = "cliente_bloqueio"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    blocked_cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", foreign_keys=[cliente_id], back_populates="cliente_bloqueios")
    blocked_cliente = relationship("Cliente", foreign_keys=[blocked_cliente_id], back_populates="cliente_bloqueios_blocked")


class TimelineClientesBloqueado(Base):
    """
    Timeline-specific blocking
    Port from TimelineClientesBloqueado.pm
    """
    __tablename__ = "timeline_clientes_bloqueados"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    block_cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", foreign_keys=[cliente_id], back_populates="timeline_clientes_bloqueados_made")
    block_cliente = relationship("Cliente", foreign_keys=[block_cliente_id], back_populates="timeline_clientes_bloqueados_blocked")


class ClientesReport(Base):
    """
    User reporting - when one user reports another
    Port from ClientesReport.pm
    """
    __tablename__ = "clientes_reports"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    reported_cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", foreign_keys=[cliente_id], back_populates="clientes_reports_made")
    reported_cliente = relationship("Cliente", foreign_keys=[reported_cliente_id], back_populates="clientes_reports_received")

