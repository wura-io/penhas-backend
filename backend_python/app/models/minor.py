from sqlalchemy import Column, String, BigInteger, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from sqlalchemy.dialects.postgresql import UUID

class AdminBigNumber(Base):
    __tablename__ = "admin_big_numbers"

    id = Column(BigInteger, primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="draft")
    sort = Column(BigInteger)
    created_on = Column(DateTime(timezone=True))
    modified_on = Column(DateTime(timezone=True))
    label = Column(String(200), nullable=False)
    comment = Column(String(200))
    sql = Column(Text, nullable=False)
    background_class = Column(String(100), nullable=False, default="bg-light")
    text_class = Column(String(100), nullable=False, default="text-dark")
    owner_new = Column(UUID(as_uuid=True))
    modified_by_new = Column(UUID(as_uuid=True))

class Badge(Base):
    __tablename__ = "badges"

    id = Column(BigInteger, primary_key=True, index=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    icon_url = Column(String(255))
    linked_cep_cidade = Column(String(200))

class BadgeInvite(Base):
    __tablename__ = "badge_invites"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    badge_id = Column(BigInteger, ForeignKey("badges.id"), nullable=False)
    token = Column(String(200), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime(timezone=True))

    cliente = relationship("Cliente")
    badge = relationship("Badge")

class ClienteTag(Base):
    __tablename__ = "cliente_tag"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    badge_id = Column(BigInteger, ForeignKey("badges.id"))
    valid_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente")
    badge = relationship("Badge")

class Preference(Base):
    __tablename__ = "preferences"

    id = Column(BigInteger, primary_key=True, index=True)
    active = Column(Boolean, default=True, nullable=False)
    name = Column(String(200), nullable=False, unique=True)
    label = Column(String(200), nullable=False)
    initial_value = Column(Boolean, default=False, nullable=False)
    sort = Column(BigInteger, default=0, nullable=False)
    admin_only = Column(Boolean, default=False, nullable=False)

class ClientesPreference(Base):
    __tablename__ = "clientes_preferences"

    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    preference_id = Column(BigInteger, ForeignKey("preferences.id"), nullable=False)
    value = Column(Boolean, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    cliente = relationship("Cliente")
    preference = relationship("Preference")

class ClientesAudiosEvento(Base):
    __tablename__ = "clientes_audios_eventos"

    id = Column(String(36), primary_key=True) # UUID
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False)
    total_bytes = Column(BigInteger, default=0)
    audio_duration = Column(BigInteger, default=0)
    requested_by_user = Column(Boolean, default=False)

    cliente = relationship("Cliente", back_populates="clientes_audios_eventos")
    audios = relationship("ClientesAudio", back_populates="evento")

class FaqTelaSobre(Base):
    __tablename__ = "faq_tela_sobre"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content_html = Column(Text)
    status = Column(String(20), nullable=False, default="draft")
    sort = Column(BigInteger, default=0)
    fts_categoria_id = Column(BigInteger, ForeignKey("faq_tela_sobre_categoria.id"))
    exibir_titulo_inline = Column(Boolean, default=False)

    fts_categoria = relationship("FaqTelaSobreCategoria")

class FaqTelaSobreCategoria(Base):
    __tablename__ = "faq_tela_sobre_categoria"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="draft")
    sort = Column(BigInteger, default=0)
    is_test = Column(Boolean, default=False)

class FaqTelaGuardiao(Base):
    __tablename__ = "faq_tela_guardiao"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content_html = Column(Text)
    status = Column(String(20), nullable=False, default="draft")
    sort = Column(BigInteger, default=0)

class Configuraco(Base):
    __tablename__ = "configuracoes"

    id = Column(BigInteger, primary_key=True, index=True)
    chave = Column(String(200), nullable=False, unique=True)
    valor = Column(Text)
    # The Perl code uses get_column('texto_faq_index'), implying columns named after keys or row-based.
    # Reading Controller/WebFAQ.pm: $c->schema2->resultset('Configuraco')->get_column('texto_faq_index')->next()
    # This implies the table has columns like 'texto_faq_index'. 
    # Let's assume a row-based key-value store OR a single row with many columns.
    # Given 'get_column' on resultset, it might be a single row table.
    texto_faq_index = Column(Text)
    texto_faq_contato = Column(Text)
    texto_conta_exclusao = Column(Text)
    privacidade = Column(Text)
    termos_de_uso = Column(Text)
    
class MfTarefa(Base):
    __tablename__ = "mf_tarefas"
    
    id = Column(BigInteger, primary_key=True, index=True)
    titulo = Column(String(512), nullable=False)
    descricao = Column(String(2048), nullable=False)
    agrupador = Column(String(120), nullable=False)
    token = Column(String(120), nullable=False)
    checkbox_contato = Column(Boolean, default=False)
    
    # Relationships
    mf_cliente_tarefas = relationship("MfClienteTarefa", back_populates="mf_tarefa")

class MfClienteTarefa(Base):
    __tablename__ = "mf_cliente_tarefas"
    
    id = Column(BigInteger, primary_key=True, index=True)
    cliente_id = Column(BigInteger, ForeignKey("clientes.id"), nullable=False)
    mf_tarefa_id = Column(BigInteger, ForeignKey("mf_tarefas.id")) # Optional if custom?
    titulo = Column(String(512))
    descricao = Column(String(2048))
    status = Column(String(20), default="pending")
    checkbox_feito = Column(Boolean, default=False)
    campo_livre = Column(Text) # JSON
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    cliente = relationship("Cliente", back_populates="mf_cliente_tarefas")
    mf_tarefa = relationship("MfTarefa", back_populates="mf_cliente_tarefas")

