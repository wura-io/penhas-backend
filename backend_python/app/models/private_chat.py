"""
Private chat between users models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text, Boolean, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class PrivateChatSessionMetadata(Base):
    """
    Private chat session metadata between two users
    Port from PrivateChatSessionMetadata.pm
    """
    __tablename__ = "private_chat_session_metadata"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id_1 = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    cliente_id_2 = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente_1 = relationship("Cliente", foreign_keys=[cliente_id_1])
    cliente_2 = relationship("Cliente", foreign_keys=[cliente_id_2])


class ChatClientesNotification(Base):
    """
    Chat notifications for users
    Port from ChatClientesNotification.pm
    """
    __tablename__ = "chat_clientes_notifications"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    from_cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    message_preview = Column(Text, nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    from_cliente = relationship("Cliente", foreign_keys=[from_cliente_id])


class RelatorioChatClienteSuporte(Base):
    """
    Support chat reports
    Port from RelatorioChatClienteSuporte.pm
    """
    __tablename__ = "relatorio_chat_cliente_suporte"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    report_data = Column(Text, nullable=False)  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente")

