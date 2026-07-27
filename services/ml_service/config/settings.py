"""ML service settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """ML service configuration settings."""

    ml_port: int = 8100
    prometheus_url: str = "http://localhost:9090"
    model_path: str = "/models/lstm_v1.pt"
    retrain_interval_minutes: int = 30
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()