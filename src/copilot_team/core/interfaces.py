from abc import ABC, abstractmethod

from copilot_team.core.models import Story, StoryStatus, Task, TaskStatus


class BaseTaskStoreBackend(ABC):
    @abstractmethod
    def put_story(self, story: Story) -> None: ...

    @abstractmethod
    def get_story(self, id: str) -> Story: ...

    @abstractmethod
    def list_stories(self, status: StoryStatus | None = None) -> list[Story]: ...

    @abstractmethod
    def put_task(self, task: Task) -> None: ...

    @abstractmethod
    def get_task(self, id: str) -> Task: ...

    @abstractmethod
    def list_tasks(
        self, status: TaskStatus | None = None, story_id: str | None = None
    ) -> list[Task]: ...

    def get_next_task(self, status: TaskStatus) -> Task | None:
        next_task = next(
            (task for task in self.list_tasks(status=status)),
            None,
        )
        return next_task

    def list_non_completed_stories(self) -> list[Story]:
        stories = []
        status_search: list[StoryStatus] = [
            "in_progress",
            "ready",
            "planning",
            "created",
        ]
        for status in status_search:
            stories.extend(self.list_stories(status=status))
        return stories
