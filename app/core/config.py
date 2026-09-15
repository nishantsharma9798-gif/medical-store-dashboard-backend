from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database — works with any Postgres URL (Neon, Supabase, Hetzner, local)
    database_url: str = "postgresql://user:password@localhost:5432/medical_db"

    # Auth
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    # WhatsApp
    whatsapp_provider: str = "aisensy"  # or "gupshup"
    whatsapp_api_key: str = ""
    whatsapp_api_base_url: str = ""

    # File storage (invoice PDFs / uploaded attachments)
    storage_dir: str = "storage"

    # Email (password reset) — stub logs to console until a real provider is configured
    smtp_configured: bool = False

    # CORS
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
