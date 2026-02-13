from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Label, Select, Static

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Task
from copilot_team.tui.pydantic_form import PydanticForm


class TaskFormPanel(Vertical):
    """Panel for creating or editing a task."""

    DEFAULT_CSS = """
    TaskFormPanel {
        height: 1fr;
        width: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def __init__(self, task: Task | None = None, story_id: str | None = None) -> None:
        super().__init__()
        self._edit_task = task
        self._story_id = story_id

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        yield PydanticForm(
            model_class=Task,
            instance=self._edit_task,
            exclude={"id", "story_id"},
        )

        # Story field — requires runtime data so it cannot be auto-generated
        stories = self.task_store.list_stories()
        story_options = [(s.name, s.id) for s in stories]
        current_story_id = (
            self._edit_task.story_id if self._edit_task else self._story_id
        ) or Select.BLANK

        yield Label("Story:")
        yield Select(
            story_options,
            value=current_story_id,
            allow_blank=True,
            id="task-story",
        )

        with Static(classes="form-buttons"):
            yield Button("Save", id="btn-save", variant="primary")
            yield Button("Cancel", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "btn-save":
            self._save_task()
        elif btn_id == "btn-cancel":
            self.app.action_show_tree()  # type: ignore[attr-defined]

    def _save_task(self) -> None:
        form = self.query_one(PydanticForm)
        errors = form.validate()
        if errors:
            self.app.notify(errors[0], severity="error")
            return

        data = form.get_form_data()

        # Attach story_id from the custom Select
        story_id_val = self.query_one("#task-story", Select).value
        data["story_id"] = story_id_val if story_id_val != Select.BLANK else None

        if self._edit_task:
            task = self._edit_task.model_copy(update=data)
        else:
            task = Task(**data)

        self.task_store.put_task(task)
        self.app.notify(f"Task '{data['name']}' saved!", severity="information")
        self.app.action_show_tree()  # type: ignore[attr-defined]
