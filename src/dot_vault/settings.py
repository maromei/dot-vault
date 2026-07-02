from pathlib import Path
from typing import ClassVar
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettingsModel(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_prefix="DOT_VAULT_"
    )
    conf_dir: Path = Path.home() / ".config/dot-vault/"


@lru_cache
def get_environment_settings():
    return EnvironmentSettingsModel()


EnvironmentSettings = get_environment_settings()
