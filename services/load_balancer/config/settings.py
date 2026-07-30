"""Load balancer settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Load balancer configuration settings."""

    lb_port: int = 8000
    redis_url: str = "redis://localhost:6379"
    ml_service_url: str = "http://localhost:8100"
    trust_strategy: str = "round_robin"
    quarantine_threshold: float = 0.30
    quarantine_initial_duration: int = 60
    bootstrap_max_initial: float = 0.5
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()