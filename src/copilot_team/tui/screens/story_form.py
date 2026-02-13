from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Static

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story
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

    def __init__(self, story: Story | None = None) -> None:
        super().__init__()
        self._story = story

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

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
            self.app.action_show_tree()  # type: ignore[attr-defined]

    async def _save_story(self) -> None:
        form = self.query_one(PydanticForm)
        errors = form.validate()
        if errors:
            self.app.notify(errors[0], severity="error")
            return

        data = form.get_form_data()

        if self._story:
            story = self._story.model_copy(update=data)
        else:
            story = Story(**data)

        await self.task_store.put_story(story)
        self.app.notify(f"Story '{data['name']}' saved!", severity="information")
        self.app.action_show_tree()  # type: ignore[attr-defined]
