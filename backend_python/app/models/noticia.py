from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Noticia(Base):
    __tablename__ = "noticias"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(2000), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    display_created_time = Column(DateTime(timezone=True), nullable=False)
    hyperlink = Column(Text)
    indexed = Column(Boolean, nullable=False, default=False)
    indexed_at = Column(DateTime(timezone=True))
    rss_feed_id = Column(BigInteger, ForeignKey("rss_feeds.id"))
    author = Column(String(200))
    info = Column(JSON, nullable=False, default={})
    fonte = Column(Text)
    published = Column(String(20), default="hidden")
    logs = Column(Text)
    image_hyperlink = Column(Text)
    tags_index = Column(String(2000), nullable=False, default=",,")
    has_topic_tags = Column(Boolean, nullable=False, default=False)

    # Relationships
    rss_feed = relationship("RssFeed", back_populates="noticias")
    noticias_tags = relationship("NoticiasTag", back_populates="noticia")
    noticias_aberturas = relationship("NoticiasAbertura", back_populates="noticia")
    noticias_vitrines = relationship("NoticiasVitrine", back_populates="noticia")


class NoticiasTag(Base):
    """
    Tags for news articles
    Port from NoticiasTag.pm
    """
    __tablename__ = "noticias_tags"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    noticia_id = Column(BigInteger, ForeignKey("noticias.id"), nullable=False, index=True)
    tag_id = Column(BigInteger, ForeignKey("tags.id"), nullable=False, index=True)

    # Relationships
    noticia = relationship("Noticia", back_populates="noticias_tags")
    tag = relationship("Tag", back_populates="noticias_tags")


class NoticiasAbertura(Base):
    """
    News article opens/views tracking
    Port from NoticiasAbertura.pm
    """
    __tablename__ = "noticias_aberturas"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    noticia_id = Column(BigInteger, ForeignKey("noticias.id"), nullable=False, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    noticia = relationship("Noticia", back_populates="noticias_aberturas")
    cliente = relationship("Cliente", back_populates="noticias_aberturas")


class NoticiasVitrine(Base):
    """
    Featured news in showcase/vitrine
    Port from NoticiasVitrine.pm
    """
    __tablename__ = "noticias_vitrine"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    noticia_id = Column(BigInteger, ForeignKey("noticias.id"), nullable=False, unique=True, index=True)
    sort = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    noticia = relationship("Noticia", back_populates="noticias_vitrines")

