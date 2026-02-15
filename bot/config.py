from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    bot_token: str = Field(alias="BOT_TOKEN")
    max_emojis_per_pack: int = Field(default=200, alias="MAX_EMOJIS_PER_PACK")
    max_total_zip_mb: int = Field(default=50, alias="MAX_TOTAL_ZIP_MB")

    download_timeout: int = Field(default=30, alias="DOWNLOAD_TIMEOUT")
    download_retries: int = Field(default=3, alias="DOWNLOAD_RETRIES")
    retry_backoff_base: float = Field(default=0.5, alias="RETRY_BACKOFF_BASE")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

def load_settings() -> Settings:
    env_file = os.getenv("ENV_FILE")
    if env_file:
        load_dotenv(env_file)
    else:
        repo_env = Path(__file__).resolve().parents[1] / ".env"
        load_dotenv(repo_env)
        load_dotenv()
    return Settings.model_validate(os.environ)
