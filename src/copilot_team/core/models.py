from functools import total_ordering
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

StoryStatus = Literal["created", "planning", "ready", "in_progress", "completed"]
TaskStatus = Literal["created", "planning", "ready", "in_progress", "completed"]


class TaskChecklistItem(BaseModel):
    description: str
    completed: bool = False


@total_ordering
class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    status: StoryStatus = "created"

    @property
    def priority(self) -> int:
        status_priority = {
            "created": 0,
            "planning": 1,
            "ready": 2,
            "in_progress": 3,
            "completed": 4,
        }
        return status_priority[self.status]

    def __lt__(self, other: "Story") -> bool:
        if self.status == other.status:
            return self.name < other.name
        return self.priority < other.priority


@total_ordering
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    agent: str | None = None
    status: TaskStatus = "created"
    description: str
    checklist: list[TaskChecklistItem] = Field(default_factory=list)
    repository_name: str | None = None
    branch_name: str | None = None
    story_id: str | None = None

    @property
    def priority(self) -> int:
        status_priority = {
            "created": 0,
            "planning": 1,
            "ready": 2,
            "in_progress": 3,
            "completed": 4,
        }
        return status_priority[self.status]

    def __lt__(self, other: "Task") -> bool:
        if self.status == other.status:
            return self.name < other.name
        return self.priority < other.priority


class Agent(BaseModel):
    id: str
    name: str | None = None
    description: str
    prompt: str
    model: str | None = None
    tools: list[str] = Field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.name or f"Agent<{self.id}>"


class AgentSkill(BaseModel):
    id: str
    name: str | None = None
    description: str | None = None
    prompt: str

    @property
    def display_name(self) -> str:
        return self.name or f"AgentSkill<{self.id}>"
