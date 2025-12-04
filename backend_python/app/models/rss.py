"""
RSS feed models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text, Boolean, String, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class RssFeed(Base):
    """
    RSS feed sources
    Port from RssFeed.pm
    """
    __tablename__ = "rss_feeds"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False)
    url = Column(Text, nullable=False, unique=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    fetch_interval_minutes = Column(Integer, nullable=False, server_default=text("60"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    rss_feeds_tags = relationship("RssFeedsTag", back_populates="rss_feed")
    noticias = relationship("Noticia", back_populates="rss_feed")


class RssFeedsTag(Base):
    """
    Tags associated with RSS feeds
    Port from RssFeedsTag.pm
    """
    __tablename__ = "rss_feeds_tags"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    rss_feed_id = Column(BigInteger, ForeignKey("rss_feeds.id"), nullable=False, index=True)
    tag_id = Column(BigInteger, ForeignKey("tags.id"), nullable=False, index=True)
    
    # Relationships
    rss_feed = relationship("RssFeed", back_populates="rss_feeds_tags")
    tag = relationship("Tag", back_populates="rss_feeds_tags")

