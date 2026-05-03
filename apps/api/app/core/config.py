from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─────────── App ───────────
    APP_NAME: str = "NEXUS AI API"
    APP_ENV: Literal["dev", "staging", "production", "test"] = "dev"
    APP_DEBUG: bool = True
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # ─────────── Server ───────────
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ─────────── Database ───────────
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexus@localhost:5434/nexus_dev"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ─────────── Redis ───────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─────────── JWT / Security ───────────
    JWT_SECRET: SecretStr = Field(default=SecretStr("change-me-in-production"))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_TTL_MINUTES: int = 60
    JWT_REFRESH_TOKEN_TTL_DAYS: int = 30

    BCRYPT_ROUNDS: int = 12

    # ─────────── Tenant integration credentials encryption ───────────
    # Fernet key (urlsafe base64 32 bytes). Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    INTEGRATIONS_ENCRYPTION_KEY: SecretStr = Field(
        default=SecretStr("dGVzdF9rZXlfcGxlYXNlX2NoYW5nZV9pbl9wcm9kdWN0aW9uPT0=")
    )

    # ─────────── SMS (Eskiz.uz) ───────────
    ESKIZ_EMAIL: str = ""
    ESKIZ_PASSWORD: SecretStr = Field(default=SecretStr(""))
    ESKIZ_SENDER: str = "4546"
    SMS_MOCK: bool = True  # in dev, log codes instead of sending

    # ─────────── AI providers (skeleton — used in Phase 1) ───────────
    ANTHROPIC_API_KEY: SecretStr = Field(default=SecretStr(""))
    OPENAI_API_KEY: SecretStr = Field(default=SecretStr(""))

    # ─────────── OAuth ───────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: SecretStr = Field(default=SecretStr(""))
    TELEGRAM_BOT_TOKEN: SecretStr = Field(default=SecretStr(""))
    OAUTH_MOCK: bool = True  # in dev, accept fake tokens to ease E2E

    # ─────────── Email (SMTP) ───────────
    EMAIL_MOCK: bool = True  # in dev, log instead of sending
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: SecretStr = Field(default=SecretStr(""))
    SMTP_FROM: str = "NEXUS AI <noreply@nexusai.uz>"
    SMTP_TLS: bool = True

    # ─────────── Rate limiting ───────────
    RATE_LIMIT_PER_MINUTE: int = 100

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV == "test"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
