import pytest

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task, TaskChecklistItem
from copilot_team.core.services import TaskService


class InMemoryTaskStoreBackend(BaseTaskStoreBackend):
    """In-memory backend for testing."""

    def __init__(self) -> None:
        self._stories: dict[str, Story] = {}
        self._tasks: dict[str, Task] = {}

    async def put_story(self, story: Story) -> None:
        self._stories[story.id] = story

    async def get_story(self, id: str) -> Story:
        return self._stories[id]

    async def list_stories(self, status=None) -> list[Story]:
        stories = list(self._stories.values())
        if status:
            stories = [s for s in stories if s.status == status]
        return stories

    async def put_task(self, task: Task) -> None:
        self._tasks[task.id] = task

    async def get_task(self, id: str) -> Task:
        return self._tasks[id]

    async def list_tasks(self, status=None, story_id=None) -> list[Task]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        if story_id:
            tasks = [t for t in tasks if t.story_id == story_id]
        return tasks


@pytest.fixture
def task_store() -> InMemoryTaskStoreBackend:
    store = InMemoryTaskStoreBackend()
    s1 = Story(
        id="s1",
        name="Auth Story",
        description="Authentication flow",
        status="in_progress",
    )
    s2 = Story(
        id="s2",
        name="Dashboard",
        description="Main dashboard",
        status="pending",
    )

    # Use synchronous internal access for fixture setup
    store._stories[s1.id] = s1
    store._stories[s2.id] = s2

    t1 = Task(
        id="t1",
        name="Login form",
        description="Create login",
        story_id="s1",
        status="completed",
        checklist=[
            TaskChecklistItem(description="HTML", completed=True),
            TaskChecklistItem(description="Validation", completed=True),
        ],
    )
    t2 = Task(
        id="t2",
        name="Signup form",
        description="Create signup",
        story_id="s1",
        status="in_progress",
        checklist=[
            TaskChecklistItem(description="HTML", completed=True),
            TaskChecklistItem(description="Backend", completed=False),
        ],
    )
    store._tasks[t1.id] = t1
    store._tasks[t2.id] = t2
    return store


@pytest.fixture
def task_service(task_store: InMemoryTaskStoreBackend) -> TaskService:
    return TaskService(task_store)
