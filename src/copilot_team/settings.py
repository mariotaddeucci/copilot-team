from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class StoryAgent(BaseModel):
    id: str | None = None
    default_model: str = "auto"


class TaskPlannerAgent(BaseModel):
    id: str | None = None
    default_model: str = "auto"


class TaskExecutorAgent(BaseModel):
    default_model: str = "auto"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="my_prefix_")
    workdir: Path = Path("./.copilot-workdir")

    story_agent: StoryAgent = StoryAgent()
    task_planner_agent: TaskPlannerAgent = TaskPlannerAgent()
    task_executor_agent: TaskExecutorAgent = TaskExecutorAgent()
