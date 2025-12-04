"""
User activity tracking models
Port from Perl Schema2::Result
"""
from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, Text, text, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class ClientesAppActivity(Base):
    """
    Tracks user app activity timestamps
    Port from ClientesAppActivity.pm
    """
    __tablename__ = "clientes_app_activity"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, unique=True, index=True)
    last_activity = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    last_tm_activity = Column(DateTime(timezone=True), nullable=True)  # Timeline activity
    
    # Relationships
    cliente = relationship("Cliente", back_populates="clientes_app_activity", uselist=False)


class ClientesAppActivityLog(Base):
    """
    Detailed log of app activities
    Port from ClientesAppActivityLog.pm
    """
    __tablename__ = "clientes_app_activity_log"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    activity_type = Column(Text, nullable=False)
    activity_meta = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", back_populates="clientes_app_activity_logs")


class ClienteAtivacoesPanico(Base):
    """
    Panic button activation tracking
    Port from ClienteAtivacoesPanico.pm
    """
    __tablename__ = "cliente_ativacoes_panico"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    latitude = Column(Text, nullable=True)
    longitude = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)  # JSON
    
    # Relationships
    cliente = relationship("Cliente", back_populates="cliente_ativacoes_panicoes")


class ClienteAtivacoesPolicia(Base):
    """
    Police call button activation tracking
    Port from ClienteAtivacoesPolicia.pm
    """
    __tablename__ = "cliente_ativacoes_policia"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", back_populates="cliente_ativacoes_policias")


class LoginLog(Base):
    """
    Login tracking
    Port from LoginLog.pm - already exists in onboarding.py, keeping for completeness
    """
    __tablename__ = "login_log"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    remote_ip = Column(Text, nullable=False)
    app_version = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", back_populates="login_logs")


class LoginErro(Base):
    """
    Failed login attempts
    Port from LoginErro.pm
    """
    __tablename__ = "login_erro"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=True, index=True)
    email = Column(Text, nullable=True)
    remote_ip = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    error_type = Column(Text, nullable=True)
    
    # Relationships
    cliente = relationship("Cliente", back_populates="login_erros")


class DeleteLog(Base):
    """
    User deletion log
    Port from DeleteLog.pm
    """
    __tablename__ = "delete_log"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, nullable=False, index=True)  # No FK since user is deleted
    deleted_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    deleted_by = Column(Text, nullable=True)  # admin user or 'self'
    reason = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)  # JSON with user data snapshot


class ClienteMfSessionControl(Base):
    """
    Manual de Fuga session control
    Port from ClienteMfSessionControl.pm
    """
    __tablename__ = "cliente_mf_session_control"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, unique=True, index=True)
    current_questionnaire_id = Column(BigInteger, nullable=True)
    current_step = Column(Integer, nullable=True)
    session_data = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", back_populates="cliente_mf_session_control", uselist=False)


class ClienteSkill(Base):
    """
    User skills/interests
    Port from ClienteSkill.pm
    """
    __tablename__ = "cliente_skills"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    skill_id = Column(BigInteger, ForeignKey("skills.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    
    # Relationships
    cliente = relationship("Cliente", back_populates="cliente_skills")
    skill = relationship("Skill", back_populates="cliente_skills")


class Skill(Base):
    """
    Available skills/interests
    Port from Skill.pm
    """
    __tablename__ = "skills"
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    name = Column(Text, nullable=False, unique=True)
    sort = Column(Integer, nullable=False, server_default=text("0"))
    active = Column(Integer, nullable=False, server_default=text("1"))
    
    # Relationships
    cliente_skills = relationship("ClienteSkill", back_populates="skill")

