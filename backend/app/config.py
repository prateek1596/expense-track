from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./spend.db"
    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    setu_base_url: str = "https://aa-sandbox.setu.co"
    setu_consent_path: str = "/api/v1/consents"
    setu_timeout_seconds: int = 20
    setu_client_id: str = ""
    setu_client_secret: str = ""
    setu_webhook_secret: str = ""
    setu_webhook_signature_header: str = "x-setu-signature"

    frontend_origin: str = "http://localhost:5173"


settings = Settings()
