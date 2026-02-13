from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static

from copilot_team.core.models import Story
from copilot_team.core.services import TaskService
from copilot_team.tui.messages import NavigateToTree
from copilot_team.tui.pydantic_form import PydanticForm


class StoryFormPanel(Vertical):
    """Panel for creating or editing a story."""

    DEFAULT_CSS = """
    StoryFormPanel {
        height: 1fr;
        width: 1fr;
        padding: 1 2;
        overflow-y: auto;
    }
    """

    def __init__(self, task_service: TaskService, story: Story | None = None) -> None:
        super().__init__()
        self._task_service = task_service
        self._story = story

    def compose(self) -> ComposeResult:
        yield PydanticForm(
            model_class=Story,
            instance=self._story,
            exclude={"id"},
        )
        with Static(classes="form-buttons"):
            yield Button("Save", id="btn-save", variant="primary")
            yield Button("Cancel", id="btn-cancel", variant="error")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            await self._save_story()
        elif event.button.id == "btn-cancel":
            self.post_message(NavigateToTree())

    async def _save_story(self) -> None:
        form = self.query_one(PydanticForm)
        errors = form.validate()
        if errors:
            self.app.notify(errors[0], severity="error")
            return

        data = form.get_form_data()

        if self._story:
            await self._task_service.update_story(self._story.id, data)
        else:
            await self._task_service.create_story(data)

        self.app.notify(f"Story '{data['name']}' saved!", severity="information")
        self.post_message(NavigateToTree())
