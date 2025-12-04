"""
Geocoding and location models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, DateTime, Text, text, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class GeoCache(Base):
    """
    Geocoding results cache
    Port from GeoCache.pm
    """
    __tablename__ = "geo_cache"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    search_term = Column(Text, nullable=False, unique=True, index=True)
    result = Column(Text, nullable=False)  # JSON with geocoding result
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))


class Municipality(Base):
    """
    Brazilian municipalities
    Port from Municipality.pm
    """
    __tablename__ = "municipalities"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True)  # IBGE code
    name = Column(Text, nullable=False)
    state = Column(String(2), nullable=False)  # UF
    state_name = Column(Text, nullable=True)
    region = Column(Text, nullable=True)

