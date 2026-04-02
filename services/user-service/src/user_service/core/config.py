from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "usersdb"
    postgres_user: str = "user"
    postgres_password: str = "password"

    redis_host: str = "localhost"
    redis_port: int = 6379

    cache_ttl_seconds: int = 3600
    debug: bool = False
    log_level: str = "INFO"
    otlp_endpoint: str | None = None
    otel_service_name: str = "user-service"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
