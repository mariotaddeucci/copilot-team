from copilot_team.agents import BaseAgentStoreBackend
from copilot_team.settings import Settings
from copilot_team.tasks import BaseTaskStoreBackend, Task, TaskChecklistItem


class TaskPlanner:
    def _items_to_checklist(self, task: Task) -> list[TaskChecklistItem]:
        if task.checklist:
            return task.checklist
        else:
            return []

    def execute(self, task: Task) -> Task:
        task = task.model_copy()
        task.status = "enqueued"
        task.checklist = self._items_to_checklist(task)
        return task


class PlannerFactory:
    def get(self, task: Task) -> BasePlanner:
        if task.category == "task":
            return TaskPlanner()
        raise ValueError(f"No planner available for task category '{task.category}'")


class TeamManagerService:
    def __init__(
        self,
        task_store_backend: BaseTaskStoreBackend,
        agent_store_backend: BaseAgentStoreBackend,
        task_planner_factory: PlannerFactory,
        settings: Settings,
    ):
        self._tasks = task_store_backend
        self._agents = agent_store_backend
        self._settings = settings
        self._task_planner_factory = task_planner_factory

    def plan_task(self, task: Task) -> None:
        task.status = "planning"
        self._tasks.put_task(task)
        planner = self._task_planner_factory.get(task)
        sub_tasks = planner.execute(task)
        for sub_task in sub_tasks:
            self._tasks.put_task(sub_task)

    def execute_task(self, task: Task) -> None:
        task.status = "in_progress"
        self._tasks.put_task(task)
