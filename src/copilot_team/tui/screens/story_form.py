from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, StoryStatus

STORY_STATUSES: list[StoryStatus] = [
    "created",
    "planning",
    "ready",
    "in_progress",
    "completed",
]


class StoryFormScreen(Screen):
    """Screen for creating or editing a story."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, story: Story | None = None) -> None:
        super().__init__()
        self._story = story

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        title = "Edit Story" if self._story else "New Story"
        with Vertical(id="story-form"):
            yield Static(f"[bold]{title}[/bold]")
            yield Label("Name:")
            yield Input(
                value=self._story.name if self._story else "",
                placeholder="Story name",
                id="story-name",
            )
            yield Label("Description:")
            yield TextArea(
                self._story.description if self._story else "",
                id="story-description",
            )
            yield Label("Status:")
            yield Select(
                [(s, s) for s in STORY_STATUSES],
                value=self._story.status if self._story else "created",
                id="story-status",
            )
            with Static(classes="form-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save_story()
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()

    def _save_story(self) -> None:
        name = self.query_one("#story-name", Input).value.strip()
        description = self.query_one("#story-description", TextArea).text.strip()
        status = self.query_one("#story-status", Select).value

        if not name:
            self.notify("Name is required", severity="error")
            return
        if not description:
            self.notify("Description is required", severity="error")
            return

        if self._story:
            story = self._story.model_copy(
                update={"name": name, "description": description, "status": status}
            )
        else:
            story = Story(name=name, description=description, status=status)

        self.task_store.put_story(story)
        self.notify(f"Story '{name}' saved!", severity="information")
        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
