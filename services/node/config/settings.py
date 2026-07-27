"""Node settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Worker node configuration settings."""

    node_id: str = "node_1"
    node_port: int = 8001
    lb_url: str = "http://localhost:8000"
    behavior_mode: str = "honest"
    behavior_intensity: float = 0.5
    report_interval_seconds: int = 5
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()