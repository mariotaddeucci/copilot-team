from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class CoreImplementationSettings(BaseModel):
    task_store: str = "copilot_team.tasks.SqliteTaskStoreBackend"


class CoreSettings(BaseModel):
    workdir: Path = Path("/tmp/copilot-team")
    repositories: dict[str, HttpUrl] = Field(default_factory=dict)
    implementations: CoreImplementationSettings = CoreImplementationSettings()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="my_prefix_")

    app_name: str = "copilot-team"
    logger: LoggerSettings = LoggerSettings()
    core: CoreSettings = CoreSettings()
