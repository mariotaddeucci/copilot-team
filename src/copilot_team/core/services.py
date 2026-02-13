"""Service layer for story and task management.

Centralises the business logic that is shared between the TUI screens and
the Copilot SDK chat tools so that both layers go through the same code
paths.
"""

from __future__ import annotations

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, StoryStatus, Task, TaskStatus


class TaskService:
    """High-level operations on stories and tasks."""

    def __init__(self, task_store: BaseTaskStoreBackend) -> None:
        self._store = task_store

    # ── Stories ────────────────────────────────────────────

    async def list_stories(self, status: StoryStatus | None = None) -> list[Story]:
        return await self._store.list_stories(status=status)

    async def get_story(self, story_id: str) -> Story:
        return await self._store.get_story(story_id)

    async def create_story(self, data: dict) -> Story:
        story = Story(**data)
        await self._store.put_story(story)
        return story

    async def update_story(self, story_id: str, data: dict) -> Story:
        existing = await self._store.get_story(story_id)
        updated = existing.model_copy(update=data)
        await self._store.put_story(updated)
        return updated

    async def save_story(self, story: Story) -> Story:
        await self._store.put_story(story)
        return story

    # ── Tasks ─────────────────────────────────────────────

    async def list_tasks(
        self,
        status: TaskStatus | None = None,
        story_id: str | None = None,
    ) -> list[Task]:
        return await self._store.list_tasks(status=status, story_id=story_id)

    async def list_unassigned_tasks(self) -> list[Task]:
        all_tasks = await self._store.list_tasks()
        return [t for t in all_tasks if t.story_id is None]

    async def get_task(self, task_id: str) -> Task:
        return await self._store.get_task(task_id)

    async def create_task(self, data: dict) -> Task:
        task = Task(**data)
        await self._store.put_task(task)
        return task

    async def update_task(self, task_id: str, data: dict) -> Task:
        existing = await self._store.get_task(task_id)
        updated = existing.model_copy(update=data)
        await self._store.put_task(updated)
        return updated

    async def save_task(self, task: Task) -> Task:
        await self._store.put_task(task)
        return task
