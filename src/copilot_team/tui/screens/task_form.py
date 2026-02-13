from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, Select, Static, TextArea

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Task, TaskChecklistItem, TaskStatus

TASK_STATUSES: list[TaskStatus] = [
    "created",
    "planning",
    "ready",
    "in_progress",
    "completed",
]


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
        self._checklist_items: list[TaskChecklistItem] = []
        if task and task.checklist:
            self._checklist_items = [item.model_copy() for item in task.checklist]

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        stories = self.task_store.list_stories()
        story_options = [(s.name, s.id) for s in stories]

        current_story_id = (
            self._edit_task.story_id if self._edit_task else self._story_id
        ) or Select.BLANK

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
        yield Label("Agent:")
        yield Input(
            value=self._edit_task.agent if self._edit_task and self._edit_task.agent else "",
            placeholder="Agent name",
            id="task-agent",
        )
        yield Label("Repository:")
        yield Input(
            value=self._edit_task.repository_name
            if self._edit_task and self._edit_task.repository_name
            else "",
            placeholder="Repository name",
            id="task-repo",
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

        yield Label("Checklist:")
        yield Vertical(id="checklist-container")
        with Horizontal(id="checklist-add-bar"):
            yield Input(placeholder="New checklist item", id="checklist-new-input")
            yield Button("+ Add", id="btn-add-checklist", variant="success")

        with Static(classes="form-buttons"):
            yield Button("Save", id="btn-save", variant="primary")
            yield Button("Cancel", id="btn-cancel", variant="error")

    def on_mount(self) -> None:
        self._render_checklist()

    def _render_checklist(self) -> None:
        container = self.query_one("#checklist-container", Vertical)
        container.remove_children()
        for i, item in enumerate(self._checklist_items):
            row = Horizontal(classes="checklist-row")
            container.mount(row)
            row.mount(
                Checkbox(
                    item.description,
                    value=item.completed,
                    id=f"chk-{i}",
                )
            )
            row.mount(
                Button("✕", id=f"chk-del-{i}", classes="checklist-delete")
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "btn-save":
            self._save_task()
        elif btn_id == "btn-cancel":
            self.app.action_show_tree()  # type: ignore[attr-defined]
        elif btn_id == "btn-add-checklist":
            self._add_checklist_item()
        elif btn_id.startswith("chk-del-"):
            idx = int(btn_id.replace("chk-del-", ""))
            if 0 <= idx < len(self._checklist_items):
                self._checklist_items.pop(idx)
                self._render_checklist()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        chk_id = event.checkbox.id or ""
        if chk_id.startswith("chk-"):
            try:
                idx = int(chk_id.replace("chk-", ""))
                if 0 <= idx < len(self._checklist_items):
                    self._checklist_items[idx].completed = event.value
            except ValueError:
                pass

    def _add_checklist_item(self) -> None:
        inp = self.query_one("#checklist-new-input", Input)
        text = inp.value.strip()
        if not text:
            return
        self._checklist_items.append(TaskChecklistItem(description=text))
        inp.value = ""
        self._render_checklist()

    def _save_task(self) -> None:
        name = self.query_one("#task-name", Input).value.strip()
        description = self.query_one("#task-description", TextArea).text.strip()
        agent = self.query_one("#task-agent", Input).value.strip() or None
        repo = self.query_one("#task-repo", Input).value.strip() or None
        status = self.query_one("#task-status", Select).value
        story_id_val = self.query_one("#task-story", Select).value
        story_id = story_id_val if story_id_val != Select.BLANK else None

        if not name:
            self.app.notify("Name is required", severity="error")
            return
        if not description:
            self.app.notify("Description is required", severity="error")
            return

        if self._edit_task:
            task = self._edit_task.model_copy(
                update={
                    "name": name,
                    "description": description,
                    "agent": agent,
                    "repository_name": repo,
                    "status": status,
                    "story_id": story_id,
                    "checklist": self._checklist_items,
                }
            )
        else:
            task = Task(
                name=name,
                description=description,
                agent=agent,
                repository_name=repo,
                status=status,
                story_id=story_id,
                checklist=self._checklist_items,
            )

        self.task_store.put_task(task)
        self.app.notify(f"Task '{name}' saved!", severity="information")
        self.app.action_show_tree()  # type: ignore[attr-defined]
