from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, Float, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from geoalchemy2 import Geography

class PontoApoio(Base):
    __tablename__ = "ponto_apoio"

    id = Column(BigInteger, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="disabled")
    created_on = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    nome = Column(String(255), nullable=False)
    natureza = Column(String(20), nullable=False)
    categoria = Column(BigInteger, nullable=False) # ForeignKey("ponto_apoio_categoria.id")
    descricao = Column(Text)
    tipo_logradouro = Column(String(20), nullable=False)
    nome_logradouro = Column(String(255), nullable=False)
    numero = Column(BigInteger)
    bairro = Column(String(255), nullable=False)
    municipio = Column(String(255), nullable=False)
    uf = Column(String(2), nullable=False)
    cep = Column(String(8), nullable=False)
    latitude = Column(Numeric(22, 6))
    longitude = Column(Numeric(22, 6))
    geog = Column(Geography(geometry_type='POINT', srid=4326))
    avaliacao = Column(Float, default=0, nullable=False)
    
    # Relationships
    categoria_rel = relationship("PontoApoioCategoria", foreign_keys=[categoria])
    ponto_apoio_2projetos = relationship("PontoApoio2projeto", back_populates="ponto_apoio")
    avaliacoes = relationship("ClientePontoApoioAvaliacao", back_populates="ponto_apoio")


class PontoApoioCategoria(Base):
    """
    Support point categories
    Port from PontoApoioCategoria.pm
    """
    __tablename__ = "ponto_apoio_categoria"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(200), nullable=False, unique=True)
    color = Column(String(20), nullable=True)
    icon = Column(String(100), nullable=True)
    is_test = Column(Boolean, nullable=False, default=False)


class PontoApoioProjeto(Base):
    """
    Support point projects
    Port from PontoApoioProjeto.pm
    """
    __tablename__ = "ponto_apoio_projeto"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(200), nullable=False, unique=True)
    descricao = Column(Text, nullable=True)
    is_test = Column(Boolean, nullable=False, default=False)

    # Relationships
    ponto_apoio_2projetos = relationship("PontoApoio2projeto", back_populates="projeto")


class PontoApoio2projeto(Base):
    """
    Many-to-many relationship between support points and projects
    Port from PontoApoio2projeto.pm
    """
    __tablename__ = "ponto_apoio_2_projeto"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    ponto_apoio_id = Column(BigInteger, ForeignKey("ponto_apoio.id"), nullable=False, index=True)
    projeto_id = Column(BigInteger, ForeignKey("ponto_apoio_projeto.id"), nullable=False, index=True)

    # Relationships
    ponto_apoio = relationship("PontoApoio", back_populates="ponto_apoio_2projetos")
    projeto = relationship("PontoApoioProjeto", back_populates="ponto_apoio_2projetos")


class PontoApoioSugestoe(Base):
    """
    Support point suggestions from users
    Port from PontoApoioSugestoe.pm
    """
    __tablename__ = "ponto_apoio_sugestoes"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    categoria_id = Column(BigInteger, ForeignKey("ponto_apoio_categoria.id"), nullable=True)
    endereco = Column(Text, nullable=True)
    observacao = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Text, nullable=True)

    # Relationships
    cliente = relationship("Cliente", back_populates="ponto_apoio_sugestoes")
    categoria = relationship("PontoApoioCategoria")


class PontoApoioSugestoesV2(Base):
    """
    Support point suggestions V2 (extended version)
    Port from PontoApoioSugestoesV2.pm
    """
    __tablename__ = "ponto_apoio_sugestoes_v2"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    categoria_id = Column(BigInteger, ForeignKey("ponto_apoio_categoria.id"), nullable=True)
    tipo_logradouro = Column(String(20), nullable=True)
    nome_logradouro = Column(String(255), nullable=True)
    numero = Column(String(50), nullable=True)
    complemento = Column(String(255), nullable=True)
    bairro = Column(String(255), nullable=True)
    municipio = Column(String(255), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(8), nullable=True)
    telefone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    horario_funcionamento = Column(Text, nullable=True)
    observacao = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(Text, nullable=True)

    # Relationships
    cliente = relationship("Cliente")
    categoria = relationship("PontoApoioCategoria")


class PontoApoioKeywordsLog(Base):
    """
    Search keywords log for support points
    Port from PontoApoioKeywordsLog.pm
    """
    __tablename__ = "ponto_apoio_keywords_log"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    keywords = Column(Text, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=True)

    # Relationships
    cliente = relationship("Cliente")


class ClientePontoApoioAvaliacao(Base):
    """
    User ratings for support points
    Port from ClientePontoApoioAvaliacao.pm
    """
    __tablename__ = "cliente_ponto_apoio_avaliacao"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False, index=True)
    ponto_apoio_id = Column(BigInteger, ForeignKey("ponto_apoio.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comentario = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    cliente = relationship("Cliente", back_populates="cliente_ponto_apoio_avaliacaos")
    ponto_apoio = relationship("PontoApoio", back_populates="avaliacoes")

