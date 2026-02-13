from abc import ABC, abstractmethod

from copilot_team.core.models import Story, StoryStatus, Task, TaskStatus


class BaseTaskStoreBackend(ABC):
    @abstractmethod
    async def put_story(self, story: Story) -> None: ...

    @abstractmethod
    async def get_story(self, id: str) -> Story: ...

    @abstractmethod
    async def list_stories(self, status: StoryStatus | None = None) -> list[Story]: ...

    @abstractmethod
    async def put_task(self, task: Task) -> None: ...

    @abstractmethod
    async def get_task(self, id: str) -> Task: ...

    @abstractmethod
    async def list_tasks(
        self, status: TaskStatus | None = None, story_id: str | None = None
    ) -> list[Task]: ...

    async def get_next_task(self, status: TaskStatus) -> Task | None:
        next_task = next(
            (task for task in await self.list_tasks(status=status)),
            None,
        )
        return next_task

    async def list_non_completed_stories(self) -> list[Story]:
        stories = []
        status_search: list[StoryStatus] = [
            "in_progress",
            "ready",
            "planning",
            "pending",
        ]
        for status in status_search:
            partia_stories = await self.list_stories(status=status)
            stories.extend(partia_stories)
        return stories
