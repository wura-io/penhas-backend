from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, computed_field
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings - compatible with Perl API configuration
    """
    # API Info
    PROJECT_NAME: str = "Penhas API"
    API_V1_STR: str = ""  # No /api/v1 prefix to match Perl routes
    
    # JWT Settings
    SECRET_KEY: str = "changethis"  # Should match Perl's JWT key from database
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days (not used with session-based JWT)
    
    # Database Settings
    POSTGRESQL_HOST: str = "localhost"
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_USER: str = "postgres"
    POSTGRESQL_PASSWORD: str = "trustme"
    POSTGRESQL_DBNAME: str = "penhas_dev"

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRESQL_USER,
            password=self.POSTGRESQL_PASSWORD,
            host=self.POSTGRESQL_HOST,
            port=self.POSTGRESQL_PORT,
            path=self.POSTGRESQL_DBNAME,
        )
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_NS: str = "penhas:"  # Namespace prefix for Redis keys
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # External Services
    GOOGLE_GEOCODE_API: Optional[str] = None
    GOOGLE_MAPS_API_KEY: Optional[str] = None  # Alias for geocoding
    
    GEOCODE_USE_HERE_API: bool = False
    GEOCODE_HERE_APP_ID: Optional[str] = None
    GEOCODE_HERE_APP_CODE: Optional[str] = None
    HERE_API_KEY: Optional[str] = None  # Modern HERE API key
    
    IWEB_SERVICE_CHAVE: Optional[str] = None  # CPF validation
    IWEBSERVICE_CPF_TOKEN: Optional[str] = None  # Alias for CPF validation
    
    AWS_SNS_KEY: Optional[str] = None
    AWS_SNS_SECRET: Optional[str] = None
    AWS_SNS_ENDPOINT: str = "http://sns.sa-east-1.amazonaws.com"
    AWS_SNS_REGION: str = "sa-east-1"
    
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_REGION: str = "sa-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    FIREBASE_SERVER_KEY: Optional[str] = None  # For FCM push notifications
    
    # Email/SMTP Settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@penhas.app.br"
    SMTP_FROM_NAME: str = "PenhaS"
    SMTP_TLS: bool = True
    
    # Frontend URL (for email links)
    FRONTEND_URL: str = "https://app.penhas.com.br"
    
    # Redis config (additional fields)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_NAMESPACE: str = "penhas:"
    
    # JWT Session config
    JWT_SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 30  # 30 days
    JWT_SECRET_KEY_COOKIES: Optional[str] = None  # For cookie-based auth if needed
    
    # App Settings
    CPF_CACHE_HASH_SALT: str = "changethis"  # Must match Perl
    MEDIA_CACHE_DIR: str = "/tmp/media"
    AVATAR_PADRAO_URL: str = "/avatar/padrao.svg"
    AVATAR_ANONIMO_URL: str = "/avatar/anonimo.svg"
    
    NOTIFICATIONS_ENABLED: bool = False
    
    # Feature Flags
    ENABLE_MANUAL_FUGA: bool = False
    ENABLE_MANUAL_FUGA_IDS: str = ""  # Comma-separated user IDs
    
    # Rate Limiting
    SUPPRESS_USER_ACTIVITY: bool = False
    
    # Testing
    HARNESS_ACTIVE: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

