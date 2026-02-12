from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import BaseModel, Field


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


class BaseAgentStoreBackend(ABC):
    @abstractmethod
    def add_agent(self, agent: Agent) -> None:
        pass

    @abstractmethod
    def get_agent(self, id: str) -> Agent:
        pass

    @abstractmethod
    def list_agents(self) -> list[Agent]:
        pass

    @abstractmethod
    def add_agent_skill(self, agent_skill: AgentSkill) -> None:
        pass

    @abstractmethod
    def get_agent_skill(self, id: str) -> AgentSkill:
        pass

    @abstractmethod
    def list_agent_skills(self) -> list[AgentSkill]:
        pass


class AgentNotFoundError(Exception):
    pass


class PathAgentStoreBackend(BaseAgentStoreBackend):
    def __init__(self, agent_path: Path, skill_path: Path):
        self._agent_path = agent_path.absolute()
        self._skill_path = skill_path.absolute()

    def _parse_agent_file(self, file_path: Path) -> Agent:
        # Implementation to parse agent file and return an Agent instance
        pass

    def _parse_agent_skill_file(self, file_path: Path) -> AgentSkill:
        # Implementation to parse agent skill file and return an AgentSkill instance
        pass

    def add_agent(self, agent: Agent) -> None:
        raise NotImplementedError("Method not implemented yet")

    def get_agent(self, id: str) -> Agent:
        agent_file = self._agent_path / f"{id}.agent.md"
        if not agent_file.exists():
            raise AgentNotFoundError(
                f"Agent with id '{id}' not found at path '{self._agent_path}'"
            )
        return self._parse_agent_file(agent_file)

    def list_agents(self) -> list[Agent]:
        agents = [
            self._parse_agent_file(agent_file)
            for agent_file in self._agent_path.glob("*.agent.md")
        ]
        return agents

    def add_agent_skill(self, agent_skill: AgentSkill) -> None:
        raise NotImplementedError("Method not implemented yet")

    def get_agent_skill(self, id: str) -> AgentSkill:
        skill_file = self._skill_path / id / "SKILL.md"
        if not skill_file.exists():
            raise AgentNotFoundError(
                f"Agent skill with id '{id}' not found at path '{self._skill_path}'"
            )
        return self._parse_agent_skill_file(skill_file)

    def list_agent_skills(self) -> list[AgentSkill]:
        agent_skills = [
            self._parse_agent_skill_file(skill_file)
            for skill_file in self._skill_path.glob("*/SKILL.md")
        ]
        return agent_skills
