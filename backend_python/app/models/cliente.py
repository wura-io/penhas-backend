from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, Text, ARRAY, text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from app.db.base_class import Base

if TYPE_CHECKING:
    from .admin import BadgeInvite, NotificationLog
    from .chat import ChatSupport, ChatSupportMessage
    from .guardiao import ClientesGuardio
    from .media import MediaUpload
    from .minor import (
        ClienteTag, ClientesPreference, ClientesAudiosEvento,
        MfClienteTarefa, Badge, Preference, Configuraco
    )
    from .noticia import NoticiasAbertura
    from .onboarding import ClientesResetPassword, LoginLog, LoginErro, ClientesActiveSession
    from .ponto_apoio import ClientePontoApoioAvaliacao, PontoApoioSugestoe
    from .quiz import ClientesQuizSession
    from .tweet import Tweet, TweetLikes, TweetsReport

class Cliente(Base):
    """
    Main user/cliente model - complete port from Perl Schema2::Result::Cliente
    100% compatible with existing Perl API database structure
    """
    __tablename__ = "clientes"

    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    
    # ============================================
    # BASIC INFO
    # ============================================
    status = Column(String(20), nullable=False, server_default=text("'setup'"))
    created_on = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    cpf_hash = Column(String(200), nullable=False, unique=True, index=True)
    cpf_prefix = Column(String(200), nullable=False)
    dt_nasc = Column(Date, nullable=False)
    email = Column(String(200), nullable=False, unique=True, index=True)
    
    # ============================================
    # ADDRESS INFO
    # ============================================
    cep = Column(String(8), nullable=False)
    cep_cidade = Column(String(200), nullable=True)
    cep_estado = Column(String(200), nullable=True)
    
    # ============================================
    # PERSONAL INFO
    # ============================================
    genero = Column(String(100), nullable=False)
    genero_outro = Column(String(200), nullable=True)
    raca = Column(String(100), nullable=True)
    minibio = Column(String(2200), nullable=True)
    nome_completo = Column(String(200), nullable=False)
    apelido = Column(String(200), nullable=False)
    nome_social = Column(String(200), nullable=True)
    avatar_url = Column(String(200), nullable=True)
    
    # ============================================
    # LOGIN & SECURITY
    # ============================================
    login_status = Column(String(20), server_default=text("'OK'"), nullable=True)
    login_status_last_blocked_at = Column(DateTime(timezone=True), nullable=True)
    senha_sha256 = Column(String(200), nullable=False)
    salt_key = Column(String(10), nullable=False)
    qtde_login_senha_normal = Column(BigInteger, server_default=text("1"), nullable=False)
    qtde_login_offline = Column(Integer, server_default=text("0"), nullable=False)
    
    # ============================================
    # VIOLENCE & SAFETY MODES
    # ============================================
    ja_foi_vitima_de_violencia = Column(Boolean, nullable=True)
    ja_foi_vitima_de_violencia_atualizado_em = Column(DateTime(timezone=True), nullable=True)
    modo_camuflado_ativo = Column(Boolean, nullable=False, server_default=text("false"))
    modo_camuflado_atualizado_em = Column(DateTime(timezone=True), nullable=True)
    modo_anonimo_ativo = Column(Boolean, nullable=False, server_default=text("false"))
    modo_anonimo_atualizado_em = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================
    # QUIZ & VIOLENCE DETECTION
    # ============================================
    quiz_detectou_violencia = Column(Boolean, nullable=True)
    quiz_detectou_violencia_atualizado_em = Column(DateTime(timezone=True), nullable=True)
    primeiro_quiz_detectou_violencia = Column(Boolean, nullable=True)
    primeiro_quiz_detectou_violencia_atualizado_em = Column(DateTime(timezone=True), nullable=True)
    quiz_assistant_yes_count = Column(BigInteger, server_default=text("0"), nullable=False)
    
    # ============================================
    # GUARDIANS & POLICE
    # ============================================
    qtde_guardioes_ativos = Column(BigInteger, server_default=text("0"), nullable=False)
    qtde_ligar_para_policia = Column(BigInteger, server_default=text("0"), nullable=False)
    
    # ============================================
    # CHAT COUNTERS
    # ============================================
    private_chat_messages_sent = Column(BigInteger, server_default=text("0"), nullable=False)
    support_chat_messages_sent = Column(BigInteger, server_default=text("0"), nullable=False)
    
    # ============================================
    # ADMIN & UPLOAD
    # ============================================
    eh_admin = Column(Boolean, nullable=False, server_default=text("false"))
    upload_status = Column(String(20), server_default=text("'ok'"), nullable=True)
    
    # ============================================
    # SKILLS & CACHED DATA
    # ============================================
    skills_cached = Column(Text, nullable=True)
    
    # ============================================
    # DELETION MANAGEMENT
    # ============================================
    perform_delete_at = Column(DateTime(timezone=True), nullable=True)
    deleted_scheduled_meta = Column(Text, nullable=True)
    deletion_started_at = Column(DateTime(timezone=True), nullable=True)
    
    # ============================================
    # TIMELINE BLOCKING (PostgreSQL Array)
    # ============================================
    timeline_clientes_bloqueados_ids = Column(
        ARRAY(Integer), 
        nullable=False, 
        server_default=text("'{}'::integer[]")
    )
    
    # ============================================
    # MANUAL DE FUGA (Escape Manual)
    # ============================================
    ja_completou_mf = Column(Boolean, server_default=text("false"), nullable=True)
    
    # ============================================
    # BUSINESS LOGIC METHODS
    # ============================================
    
    def is_female(self) -> bool:
        """Check if user is female (Feminino or MulherTrans) - matches Perl logic"""
        return self.genero in ("Feminino", "MulherTrans")
    
    def access_modules_str(self) -> str:
        """Return comma-separated string of accessible modules - matches Perl logic"""
        modules = self.get_access_modules()
        return ',' + ','.join(modules.keys()) + ','
    
    def get_access_modules(self) -> dict[str, dict]:
        """
        Return dictionary of accessible modules based on gender
        Matches Perl's _build_access_modules logic
        """
        import os
        modules: dict[str, dict] = {}
        if self.is_female():
            for module in ['tweets', 'chat_privado', 'chat_suporte', 'pontos_de_apoio', 'modo_seguranca', 'noticias']:
                modules[module] = {}
            
            # Manual de Fuga conditionally (based on ENV config)
            enable_mf = os.getenv('ENABLE_MANUAL_FUGA')
            enable_mf_ids = os.getenv('ENABLE_MANUAL_FUGA_IDS', '')
            if enable_mf or (enable_mf_ids and f",{self.id}," in f",{enable_mf_ids},"):
                modules['mf'] = {}
        else:
            for module in ['chat_suporte', 'pontos_de_apoio', 'noticias']:
                modules[module] = {}
        return modules
    
    def access_modules_as_config(self) -> list:
        """
        Return modules with metadata configuration
        Matches Perl's access_modules_as_config method
        """
        meta = {
            'chat_privado': {'polling_rate': '20'},
            'chat_suporte': {'polling_rate': '20'},
            'modo_seguranca': {
                'numero': '190',
                'audio_each_duration': '901',
                'audio_full_duration': '901',
            },
            'tweets': {'max_length': 2200},
            'mf': {'max_checkbox_contato': 3},
        }
        
        modules = self.get_access_modules()
        return [{'code': key, 'meta': meta.get(key, {})} for key in modules.keys()]
    
    def has_module(self, module: str) -> bool:
        """Check if user has access to a specific module - matches Perl logic"""
        return f",{module}," in self.access_modules_str()
    
    def avatar_url_or_default(self, default_url: Optional[str] = None) -> str:
        """Return avatar URL or default - matches Perl logic"""
        import os
        return self.avatar_url or default_url or os.getenv('AVATAR_PADRAO_URL', '')
    
    def support_chat_auth(self) -> str:
        """Generate support chat auth token - matches Perl logic"""
        return 'S' + self.cpf_hash[:4]
    
    def assistant_session_id(self) -> str:
        """Generate assistant session ID - matches Perl logic"""
        return 'A' + self.cpf_hash[:4]
    
    def mf_assistant_session_id(self) -> str:
        """Generate Manual de Fuga assistant session ID - matches Perl logic"""
        return 'MF' + self.cpf_hash[:4]
    
    def mf_redo_addr_session_id(self) -> str:
        """Generate MF address redo session ID - matches Perl logic"""
        return 'MF:Address' + self.cpf_hash[:4]
    
    def name_for_admin(self) -> str:
        """Return formatted name for admin display - matches Perl logic"""
        return f"{self.apelido} ({self.nome_completo})"
    
    def cep_formatted(self) -> str:
        """Return formatted CEP (ZIP code) like 12345-678 - matches Perl logic"""
        cep = self.cep
        if len(cep) == 8:
            return f"{cep[:5]}-{cep[5:]}"
        return cep
    
    def id_composed_fk(self, other_id) -> str:
        """Return string for composed foreign key - matches Perl logic"""
        return f"{self.id}:{other_id}"
