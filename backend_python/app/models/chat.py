from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID

class ChatSupport(Base):
    __tablename__ = "chat_support"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, unique=True)
    last_msg_is_support = Column(Boolean, nullable=False, default=False)
    last_msg_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True))
    last_msg_preview = Column(String(200))
    last_msg_by = Column(String(200))

    cliente = relationship("Cliente")
    messages = relationship("ChatSupportMessage", back_populates="chat_support")

class ChatSupportMessage(Base):
    __tablename__ = "chat_support_message"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"))
    created_at = Column(DateTime(timezone=True))
    chat_support_id = Column(BigInteger, ForeignKey("chat_support.id"), nullable=False)
    admin_user_id_directus8 = Column(BigInteger)
    message = Column(Text, nullable=False)
    admin_user_id = Column(UUID(as_uuid=True))

    chat_support = relationship("ChatSupport", back_populates="messages")
    cliente = relationship("Cliente")

