"""
Pydantic Settings — loads from .env / environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    # Render provides DATABASE_URL as a single connection string.
    # For local dev, we fall back to building it from individual DB_* vars.
    database_url_env: str = ""  # mapped from DATABASE_URL env var

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "EMSNew"
    db_user: str = "postgres"
    db_password: str = "1234"

    @property
    def database_url(self) -> str:
        # If Render provides DATABASE_URL, use it (convert postgres:// to postgresql+psycopg2://)
        if self.database_url_env:
            url = self.database_url_env
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        # Otherwise build from individual vars (local dev)
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ── JWT ────────────────────────────────────────────────────────────────────
    jwt_secret: str = "Z3V2d3dxd3Vpd2V1d2V1aXdlcXVpd2V1cXVpd2V1cXVpd2V1"
    jwt_access_expiration_ms: int = 900_000          # 15 min
    jwt_refresh_expiration_ms: int = 8_640_000_000   # 100 days

    # ── Email ──────────────────────────────────────────────────────────────────
    mail_username: str = ""
    mail_password: str = ""
    mail_host: str = "smtp.gmail.com"
    mail_port: int = 587

    # ── CORS ───────────────────────────────────────────────────────────────────
    cors_allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    # ── Cookie ─────────────────────────────────────────────────────────────────
    cookie_secure: bool = False
    cookie_same_site: str = "Lax"

    # ── Chatbot ────────────────────────────────────────────────────────────────
    groq_api_key: str = ""

    # ── Server ─────────────────────────────────────────────────────────────────
    port: int = 8000

    # ── Default page size (Spring Data compatible) ─────────────────────────────
    default_page_size: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

        # Map DATABASE_URL env var to our field name
        fields = {
            "database_url_env": {"env": "DATABASE_URL"},
        }


settings = Settings()
