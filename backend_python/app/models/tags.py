"""
Tags and content categorization models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text, Boolean, String, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Tag(Base):
    """
    Content tags (for news, tweets, etc.)
    Port from Tag.pm
    """
    __tablename__ = "tags"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(Text, nullable=False, unique=True)
    is_test = Column(Boolean, nullable=False, server_default=text("false"))
    
    # Relationships
    noticias_tags = relationship("NoticiasTag", back_populates="tag")
    rss_feeds_tags = relationship("RssFeedsTag", back_populates="tag")


class MfTag(Base):
    """
    Manual de Fuga specific tags
    Port from MfTag.pm
    """
    __tablename__ = "mf_tags"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    title = Column(Text, nullable=False, unique=True)
    is_test = Column(Boolean, nullable=False, server_default=text("false"))


class TagsHighlight(Base):
    """
    Highlighted/featured tags
    Port from TagsHighlight.pm
    """
    __tablename__ = "tags_highlight"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    tag_id = Column(BigInteger, ForeignKey("tags.id"), nullable=False, index=True)
    sort = Column(Integer, nullable=False, server_default=text("0"))
    active = Column(Boolean, nullable=False, server_default=text("true"))
    
    # Relationships
    tag = relationship("Tag")


class TagIndexingConfig(Base):
    """
    Tag indexing configuration
    Port from TagIndexingConfig.pm
    """
    __tablename__ = "tag_indexing_config"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    tag_id = Column(BigInteger, ForeignKey("tags.id"), nullable=False, unique=True, index=True)
    config = Column(Text, nullable=False)  # JSON configuration
    
    # Relationships
    tag = relationship("Tag")

