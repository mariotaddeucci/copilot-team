from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Label, Select, Static

from copilot_team.core.models import Task
from copilot_team.core.services import TaskService
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
    def task_service(self) -> TaskService:
        return self.app.task_service  #

    @property
    def _current_story_id(self) -> str | None:
        return self._edit_task.story_id if self._edit_task else self._story_id

    def compose(self) -> ComposeResult:
        yield PydanticForm(
            model_class=Task,
            instance=self._edit_task,
            exclude={"id", "story_id"},
        )

        # Story select — populated async in on_mount
        yield Label("Story:")
        yield Select(
            [],
            value=self._current_story_id or Select.BLANK,
            allow_blank=True,
            id="task-story",
        )

        with Static(classes="form-buttons"):
            yield Button("Save", id="btn-save", variant="primary")
            yield Button("Cancel", id="btn-cancel", variant="error")

    async def on_mount(self) -> None:
        stories = await self.task_service.list_stories()
        story_options = [(s.name, s.id) for s in stories]
        select = self.query_one("#task-story", Select)
        select.set_options(story_options)
        if self._current_story_id:
            select.value = self._current_story_id

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "btn-save":
            await self._save_task()
        elif btn_id == "btn-cancel":
            self.app.action_show_tree()  #

    async def _save_task(self) -> None:
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

        await self.task_service.save_task(task)
        self.app.notify(f"Task '{data['name']}' saved!", severity="information")
        self.app.action_show_tree()  #
