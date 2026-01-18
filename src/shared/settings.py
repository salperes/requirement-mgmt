from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "rms"
    environment: str = "local"

    database_url: str = "postgresql+psycopg2://rms:rms@localhost:5432/rms"

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    request_id_header: str = "x-request-id"

    class Config:
        env_prefix = "rms_"
        case_sensitive = False


settings = Settings()