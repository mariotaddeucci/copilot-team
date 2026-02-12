from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Task, TaskStatus

TASK_STATUSES: list[TaskStatus] = [
    "created",
    "planning",
    "ready",
    "in_progress",
    "completed",
]


class TaskFormScreen(Screen):
    """Screen for creating or editing a task."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, task: Task | None = None, story_id: str | None = None) -> None:
        super().__init__()
        self._edit_task = task
        self._story_id = story_id

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        title = "Edit Task" if self._edit_task else "New Task"

        stories = self.task_store.list_stories()
        story_options = [(s.name, s.id) for s in stories]

        current_story_id = (
            self._edit_task.story_id if self._edit_task else self._story_id
        ) or Select.BLANK

        with Vertical(id="task-form"):
            yield Static(f"[bold]{title}[/bold]")
            yield Label("Name:")
            yield Input(
                value=self._edit_task.name if self._edit_task else "",
                placeholder="Task name",
                id="task-name",
            )
            yield Label("Description:")
            yield TextArea(
                self._edit_task.description if self._edit_task else "",
                id="task-description",
            )
            yield Label("Status:")
            yield Select(
                [(s, s) for s in TASK_STATUSES],
                value=self._edit_task.status if self._edit_task else "created",
                id="task-status",
            )
            yield Label("Story:")
            yield Select(
                story_options,
                value=current_story_id,
                allow_blank=True,
                id="task-story",
            )

            if self._edit_task and self._edit_task.checklist:
                yield Label("Checklist:")
                for i, item in enumerate(self._edit_task.checklist):
                    check = "✅" if item.completed else "⬜"
                    yield Static(f"  {check} {item.description}")

            with Static(classes="form-buttons"):
                yield Button("Save", id="btn-save", variant="primary")
                yield Button("Cancel", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self._save_task()
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()

    def _save_task(self) -> None:
        name = self.query_one("#task-name", Input).value.strip()
        description = self.query_one("#task-description", TextArea).text.strip()
        status = self.query_one("#task-status", Select).value
        story_id_val = self.query_one("#task-story", Select).value
        story_id = story_id_val if story_id_val != Select.BLANK else None

        if not name:
            self.notify("Name is required", severity="error")
            return
        if not description:
            self.notify("Description is required", severity="error")
            return

        if self._edit_task:
            task = self._edit_task.model_copy(
                update={
                    "name": name,
                    "description": description,
                    "status": status,
                    "story_id": story_id,
                }
            )
        else:
            task = Task(
                name=name,
                description=description,
                status=status,
                story_id=story_id,
            )

        self.task_store.put_task(task)
        self.notify(f"Task '{name}' saved!", severity="information")
        self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
