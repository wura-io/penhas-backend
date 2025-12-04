from sqlalchemy import Column, String, BigInteger, Text, ForeignKey, DateTime, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID

class DirectusUser(Base):
    __tablename__ = "directus_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(16), nullable=False, default="draft")
    role = Column(Integer)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(128), nullable=False, unique=True)
    password = Column(String(255)) # Argon2 hash

class AdminClientesSegment(Base):
    __tablename__ = "admin_clientes_segments"

    id = Column(BigInteger, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="draft")
    created_on = Column(DateTime(timezone=True))
    modified_on = Column(DateTime(timezone=True))
    is_test = Column(Boolean, nullable=False, default=False)
    label = Column(String(200), nullable=False)
    last_count = Column(BigInteger)
    last_run_at = Column(DateTime(timezone=True))
    cond = Column(JSON, nullable=False, default={})
    attr = Column(JSON, nullable=False, default={})
    sort = Column(BigInteger, default=0, nullable=False)
    owner = Column(UUID(as_uuid=True))
    modified_by = Column(UUID(as_uuid=True))

class NotificationMessage(Base):
    __tablename__ = "notification_messages"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    icon = Column(Integer, default=0, nullable=False)
    subject_id = Column(BigInteger) # The user who triggered, or null for system
    meta = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    notification_message_id = Column(BigInteger, ForeignKey("notification_messages.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    read_at = Column(DateTime(timezone=True))

    message = relationship("NotificationMessage")
    cliente = relationship("Cliente", back_populates="notification_logs")


class ClientesAppNotification(Base):
    """
    App push notifications sent to users
    Port from ClientesAppNotification.pm
    """
    __tablename__ = "clientes_app_notifications"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    notification_message_id = Column(BigInteger, ForeignKey("notification_messages.id"), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    delivery_status = Column(String(50), nullable=False, default="sent")
    device_token = Column(Text, nullable=True)
    response = Column(Text, nullable=True)  # JSON response from FCM

    # Relationships
    cliente = relationship("Cliente", back_populates="clientes_app_notifications")
    message = relationship("NotificationMessage")

