from sqlalchemy import Column, String, BigInteger, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class MediaUpload(Base):
    __tablename__ = "media_upload"

    id = Column(String(200), primary_key=True)
    file_info = Column(Text)
    file_sha1 = Column(String(200), nullable=False)
    file_size = Column(BigInteger)
    s3_path = Column(Text, nullable=False)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    intention = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    s3_path_avatar = Column(Text)
    file_size_avatar = Column(BigInteger)

    cliente = relationship("Cliente", back_populates="media_uploads")
    clientes_audios = relationship("ClientesAudio", back_populates="media_upload")

