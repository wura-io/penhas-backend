"""
Audio recording models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text, Boolean, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class ClientesAudio(Base):
    """
    Individual audio files within an event
    Port from ClientesAudio.pm
    """
    __tablename__ = "clientes_audios"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    clientes_audios_evento_id = Column(String(36), ForeignKey("clientes_audios_eventos.id"), nullable=False, index=True)
    media_upload_id = Column(BigInteger, ForeignKey("media_uploads.id"), nullable=False)
    sequence = Column(BigInteger, nullable=False)
    audio_duration = Column(BigInteger, nullable=True)  # Duration in seconds
    waveform = Column(Text, nullable=True)  # JSON array of waveform data
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    cliente_created_at = Column(DateTime(timezone=True), nullable=True)  # Client-reported timestamp
    
    # Relationships
    cliente = relationship("Cliente")
    evento = relationship("ClientesAudiosEvento", back_populates="audios")
    media_upload = relationship("MediaUpload")

