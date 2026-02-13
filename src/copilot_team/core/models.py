from functools import total_ordering
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

StoryStatus = Literal["pending", "planning", "ready", "in_progress", "completed"]
TaskStatus = Literal["pending", "planning", "ready", "in_progress", "completed"]


class TaskChecklistItem(BaseModel):
    """Item de checklist de uma tarefa."""

    description: str = Field(description="Descrição do item do checklist")
    completed: bool = Field(default=False, description="Item concluído")


@total_ordering
class Story(BaseModel):
    """História do projeto."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Identificador único da história")
    name: str = Field(description="Nome da história")
    description: str = Field(description="Descrição detalhada da história", json_schema_extra={"widget": "textarea"})
    status: StoryStatus = Field(default="pending", description="Status atual da história")

    @property
    def priority(self) -> int:
        status_priority = {
            "pending": 0,
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
    """Tarefa do projeto."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Identificador único da tarefa")
    name: str = Field(description="Nome da tarefa")
    description: str = Field(description="Descrição detalhada da tarefa", json_schema_extra={"widget": "textarea"})
    agent: str | None = Field(default=None, description="Agente responsável pela tarefa")
    status: TaskStatus = Field(default="pending", description="Status atual da tarefa")
    repository_name: str | None = Field(default=None, description="Nome do repositório")
    branch_name: str | None = Field(default=None, description="Nome da branch")
    story_id: str | None = Field(default=None, description="ID da história associada")
    checklist: list[TaskChecklistItem] = Field(default_factory=list, description="Lista de itens do checklist")

    @property
    def priority(self) -> int:
        status_priority = {
            "pending": 0,
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
    """Configuração de um agente."""

    id: str = Field(description="Identificador único do agente")
    name: str | None = Field(default=None, description="Nome de exibição do agente")
    description: str = Field(description="Descrição do agente", json_schema_extra={"widget": "textarea"})
    prompt: str = Field(description="Prompt do agente", json_schema_extra={"widget": "textarea"})
    model: str | None = Field(default=None, description="Modelo de IA utilizado")
    tools: list[str] = Field(default_factory=list, description="Lista de ferramentas disponíveis")

    @property
    def display_name(self) -> str:
        return self.name or f"Agent<{self.id}>"


class AgentSkill(BaseModel):
    """Habilidade de um agente."""

    id: str = Field(description="Identificador único da habilidade")
    name: str | None = Field(default=None, description="Nome da habilidade")
    description: str | None = Field(default=None, description="Descrição da habilidade")
    prompt: str = Field(description="Prompt da habilidade", json_schema_extra={"widget": "textarea"})

    @property
    def display_name(self) -> str:
        return self.name or f"AgentSkill<{self.id}>"
