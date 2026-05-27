"""Application configuration via pydantic-settings."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    app_name: str = "operational-semantics-lab"
    database_url: str = "sqlite+aiosqlite:///./data/operational_semantics.db"
    log_level: str = "INFO"
    approval_ttl_minutes: int = 60
    seed_on_startup: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
