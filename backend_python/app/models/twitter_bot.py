"""
Twitter bot configuration models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, DateTime, Text, text, Boolean, String, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class TwitterBotConfig(Base):
    """
    Twitter bot configuration
    Port from TwitterBotConfig.pm
    """
    __tablename__ = "twitter_bot_config"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    bot_name = Column(String(200), nullable=False, unique=True)
    api_key = Column(Text, nullable=True)
    api_secret = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    access_token_secret = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    config = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

