import asyncio
from pathlib import Path

from copilot import CopilotClient, CopilotSession, SessionEvent

from copilot_team.agents import BaseAgentStoreBackend
from copilot_team.repository_manager import RepositoryManager
from copilot_team.settings import Settings
from copilot_team.tasks import BaseTaskStoreBackend, Task


class CopilotClientFactory:
    def __init__(self, settings: Settings):
        self._settings = settings

    def create(self) -> CopilotClient:
        return CopilotClient({"auto_restart": True, "auto_start": True})


class AgentTaskRunner:
    def __init__(
        self,
        agent_store_backend: BaseAgentStoreBackend,
        repository_manager: RepositoryManager,
        settings: Settings,
    ):
        self._agent_store_backend = agent_store_backend
        self._repository_manager = repository_manager
        self._settings = settings

    @property
    def _tmp_dir(self) -> Path:
        tmp_dir = self._settings.workdir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _get_workdir_for_task(self, task: Task) -> Path:
        if task.repository_url and task.branch_name:
            return self._repository_manager.get_worktree_path(
                url=str(task.repository_url),
                branch=task.branch_name,
            )

        tmp_dir = self._tmp_dir / task.id
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _get_agent_for_task(self, task: Task):
        if task.agent is None:
            raise NotImplementedError("Task does not have an assigned agent")

        return self._agent_store_backend.get_agent(task.agent)

    async def _create_copilot_session(self, task: Task) -> CopilotSession:
        agent = self._get_agent_for_task(task)
        model = agent.model or self._settings.task_executor_agent.default_model
        workdir = self._get_workdir_for_task(task)
        client = CopilotClient({"auto_restart": True, "auto_start": True})
        session = await client.create_session(
            {
                "model": model,
                "working_directory": workdir.absolute().as_posix(),
            }
        )
        return session

    async def execute(self, task: Task) -> None:
        task_message = "You are an autonomous agent whose goal is to complete the following task:\n"
        task_message += f"**Name**: {task.name}\n"
        task_message += f"**Description**: {task.description}\n"
        if task.checklist:
            task_message += "**Checklist**:\n"
            for item in task.checklist:
                status = "x" if item.completed else " "
                task_message += f"- [{status}] {item.description}\n"

        session = await self._create_copilot_session(task)
        finish_event = asyncio.Event()

        def on_event(event: SessionEvent) -> None:
            if event.type.value == "session.idle":
                finish_event.set()

        session.on(on_event)
        await session.send({"prompt": task_message})

        await finish_event.wait()
        await session.destroy()


class TeamManagerService:
    def __init__(
        self,
        task_planner: BaseTaskPlanner,
        task_store_backend: BaseTaskStoreBackend,
        settings: Settings,
    ):
        self._tasks = task_store_backend
        self._agents = agent_store_backend
        self._settings = settings
        self._planner = task_planner

    def plan_task(self, task: Task) -> None:
        task.status = "planning"
        self._tasks.put_task(task)
        task = self._planner.execute(task)

    def execute(self, task: Task) -> None:
        task.status = "in_progress"
        self._tasks.put_task(task)
