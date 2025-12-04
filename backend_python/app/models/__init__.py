# Import all models for SQLAlchemy to register them
# Complete port from Perl Schema2::Result

# Core user model
from app.models.cliente import Cliente

# Onboarding & Auth
from app.models.onboarding import (
    ClientesResetPassword,
    ClientesActiveSession,
    CpfErro,
)

# Activity tracking
from app.models.activity import (
    ClientesAppActivity,
    ClientesAppActivityLog,
    ClienteAtivacoesPanico,
    ClienteAtivacoesPolicia,
    LoginLog,
    LoginErro,
    DeleteLog,
    ClienteMfSessionControl,
    ClienteSkill,
    Skill,
)

# Blocking & Reporting
from app.models.blocking import (
    ClienteBloqueio,
    TimelineClientesBloqueado,
    ClientesReport,
)

# Support points
from app.models.ponto_apoio import (
    PontoApoio,
    PontoApoioCategoria,
    PontoApoioProjeto,
    PontoApoio2projeto,
    PontoApoioSugestoe,
    PontoApoioSugestoesV2,
    PontoApoioKeywordsLog,
    ClientePontoApoioAvaliacao,
)

# News/Content
from app.models.noticia import (
    Noticia,
    NoticiasTag,
    NoticiasAbertura,
    NoticiasVitrine,
)

# Guardians
from app.models.guardiao import ClientesGuardio

# Quiz
from app.models.quiz import (
    Questionnaire,
    ClientesQuizSession,
    AnonymousQuizSession,
    QuizConfig,
    MfQuestionnaireOrder,
    MfQuestionnaireRemoveTarefa,
)

# Chat
from app.models.chat import (
    ChatSupport,
    ChatSupportMessage,
)

# Private Chat
from app.models.private_chat import (
    PrivateChatSessionMetadata,
    ChatClientesNotification,
    RelatorioChatClienteSuporte,
)

# Timeline/Tweets
from app.models.tweet import (
    Tweet,
    TweetLikes,
    TweetsReport,
)

# Media
from app.models.media import MediaUpload

# Audio
from app.models.audio import ClientesAudio

# Admin
from app.models.admin import (
    DirectusUser,
    AdminClientesSegment,
    NotificationMessage,
    NotificationLog,
    ClientesAppNotification,
    AdminBigNumber,
)

# Minor/Utility models
from app.models.minor import (
    Badge,
    BadgeInvite,
    ClienteTag,
    Preference,
    ClientesPreference,
    ClientesAudiosEvento,
    FaqTelaSobre,
    FaqTelaSobreCategoria,
    FaqTelaGuardiao,
    Configuraco,
    MfTarefa,
    MfClienteTarefa,
)

# Tags
from app.models.tags import (
    Tag,
    MfTag,
    TagsHighlight,
    TagIndexingConfig,
)

# RSS
from app.models.rss import (
    RssFeed,
    RssFeedsTag,
)

# Geo
from app.models.geo import (
    GeoCache,
    Municipality,
)

# SMS & Communication
from app.models.sms import (
    SentSmsLog,
)

# Twitter Bot
from app.models.twitter_bot import TwitterBotConfig

# Export all for easy access
__all__ = [
    # Core
    "Cliente",
    # Onboarding
    "ClientesResetPassword",
    "ClientesActiveSession",
    "CpfErro",
    # Activity
    "ClientesAppActivity",
    "ClientesAppActivityLog",
    "ClienteAtivacoesPanico",
    "ClienteAtivacoesPolicia",
    "LoginLog",
    "LoginErro",
    "DeleteLog",
    "ClienteMfSessionControl",
    "ClienteSkill",
    "Skill",
    # Blocking
    "ClienteBloqueio",
    "TimelineClientesBloqueado",
    "ClientesReport",
    # Support Points
    "PontoApoio",
    "PontoApoioCategoria",
    "PontoApoioProjeto",
    "PontoApoio2projeto",
    "PontoApoioSugestoe",
    "PontoApoioSugestoesV2",
    "PontoApoioKeywordsLog",
    "ClientePontoApoioAvaliacao",
    # News
    "Noticia",
    "NoticiasTag",
    "NoticiasAbertura",
    "NoticiasVitrine",
    # Guardians
    "ClientesGuardio",
    # Quiz
    "Questionnaire",
    "ClientesQuizSession",
    "AnonymousQuizSession",
    "QuizConfig",
    "MfQuestionnaireOrder",
    "MfQuestionnaireRemoveTarefa",
    # Chat
    "ChatSupport",
    "ChatSupportMessage",
    "PrivateChatSessionMetadata",
    "ChatClientesNotification",
    "RelatorioChatClienteSuporte",
    # Timeline
    "Tweet",
    "TweetLikes",
    "TweetsReport",
    # Media
    "MediaUpload",
    "ClientesAudio",
    # Admin
    "DirectusUser",
    "AdminClientesSegment",
    "NotificationMessage",
    "NotificationLog",
    "ClientesAppNotification",
    "AdminBigNumber",
    # Minor
    "Badge",
    "BadgeInvite",
    "ClienteTag",
    "Preference",
    "ClientesPreference",
    "ClientesAudiosEvento",
    "FaqTelaSobre",
    "FaqTelaSobreCategoria",
    "FaqTelaGuardiao",
    "Configuraco",
    "MfTarefa",
    "MfClienteTarefa",
    # Tags
    "Tag",
    "MfTag",
    "TagsHighlight",
    "TagIndexingConfig",
    # RSS
    "RssFeed",
    "RssFeedsTag",
    # Geo
    "GeoCache",
    "Municipality",
    # SMS
    "SentSmsLog",
    # Twitter
    "TwitterBotConfig",
]
