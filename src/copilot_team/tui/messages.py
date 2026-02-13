"""Textual messages for cross-panel navigation."""

from __future__ import annotations

from textual.message import Message

from copilot_team.core.models import Story, Task


class NavigateToTree(Message):
    """Request navigation to the tree view panel."""


class NavigateToStoryForm(Message):
    """Request navigation to the story form panel."""

    def __init__(self, story: Story | None = None) -> None:
        self.story = story
        super().__init__()


class NavigateToTaskForm(Message):
    """Request navigation to the task form panel."""

    def __init__(self, task: Task | None = None, story_id: str | None = None) -> None:
        self.task = task
        self.story_id = story_id
        super().__init__()
