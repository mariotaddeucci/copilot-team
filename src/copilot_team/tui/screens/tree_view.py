from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task

# Column widths for the tabular layout
COL_NAME = 36
COL_AGENT = 18
COL_REPO = 22
COL_CHECK = 10
COL_STATUS = 14


def _status_icon(status: str) -> str:
    icons = {
        "created": "⬜",
        "planning": "📝",
        "ready": "🟡",
        "in_progress": "🔵",
        "completed": "✅",
    }
    return icons.get(status, "❓")


def _status_color(status: str) -> str:
    colors = {
        "created": "#6272a4",
        "planning": "#f1fa8c",
        "ready": "#ffb86c",
        "in_progress": "#8be9fd",
        "completed": "#50fa7b",
    }
    return colors.get(status, "#f8f8f2")


def _pad(text: str, width: int) -> str:
    """Pad or truncate text to exact width for alignment."""
    if len(text) >= width:
        return text[: width - 1] + "…"
    return text + " " * (width - len(text))


class StoryHeader(Static):
    """Clickable collapsible story header row."""

    def __init__(self, story: Story, expanded: bool = True) -> None:
        self._story = story
        self._expanded = expanded
        super().__init__(self._render_label(), classes="story-header")
        self.id = f"story-hdr-{story.id}"

    def _render_label(self) -> str:
        icon = _status_icon(self._story.status)
        color = _status_color(self._story.status)
        arrow = "▼" if self._expanded else "▶"
        name_text = _pad(self._story.name, COL_NAME)
        desc = self._story.description or ""
        if len(desc) > 40:
            desc = desc[:39] + "…"
        return f"[bold]{arrow}[/] {icon} [{color}]{name_text}[/] [dim]{desc}[/]"

    def toggle(self) -> bool:
        self._expanded = not self._expanded
        self.update(self._render_label())
        return self._expanded

    @property
    def story(self) -> Story:
        return self._story

    @property
    def expanded(self) -> bool:
        return self._expanded


class TaskRow(Static):
    """A single task row in tabular format."""

    def __init__(self, task: Task) -> None:
        self._data = task
        super().__init__(self._render_label(), classes="task-row")
        self.id = f"task-row-{task.id}"

    def _render_label(self) -> str:
        icon = _status_icon(self._data.status)
        color = _status_color(self._data.status)
        name = _pad(self._data.name, COL_NAME)
        agent = _pad(self._data.agent or "—", COL_AGENT)
        repo = _pad(self._data.repository_name or "—", COL_REPO)
        total = len(self._data.checklist)
        done = sum(1 for c in self._data.checklist if c.completed)
        check = _pad(f"{done}/{total}" if total else "—", COL_CHECK)
        status = _pad(self._data.status, COL_STATUS)
        return f"    {icon} [{color}]{name}[/] [dim]{agent}[/] [dim]{repo}[/] [#bd93f9]{check}[/] [{color}]{status}[/]"

    @property
    def task_data(self) -> Task:
        return self._data


class TreeViewPanel(Vertical):
    """Panel showing stories and tasks in a tabular collapsible layout."""

    DEFAULT_CSS = """
    TreeViewPanel {
        height: 1fr;
        width: 1fr;
    }
    """

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        with Horizontal(id="tree-toolbar"):
            yield Button("+ Story", id="btn-new-story", variant="primary")
            yield Button("+ Task", id="btn-new-task", variant="success")
        yield Static(self._header_row(), id="table-header")
        yield VerticalScroll(id="stories-tree")

    def _header_row(self) -> str:
        name = _pad("Name", COL_NAME + 6)
        agent = _pad("Agent", COL_AGENT)
        repo = _pad("Repository", COL_REPO)
        check = _pad("Checklist", COL_CHECK)
        status = _pad("Status", COL_STATUS)
        return f"[bold #bd93f9]{name}{agent}{repo}{check}{status}[/]"

    def on_mount(self) -> None:
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        container = self.query_one("#stories-tree", VerticalScroll)
        container.remove_children()

        stories = self.task_store.list_stories()
        stories.sort()

        for story in stories:
            header = StoryHeader(story, expanded=True)
            container.mount(header)
            tasks = self.task_store.list_tasks(story_id=story.id)
            tasks.sort()
            for task in tasks:
                container.mount(TaskRow(task))

        # Unassigned tasks section
        unassigned = [
            t for t in self.task_store.list_tasks() if t.story_id is None
        ]
        if unassigned:
            unassigned.sort()
            container.mount(
                Static(
                    "[bold #ffb86c]▼ ⚠ Unassigned Tasks[/]",
                    id="unassigned-header",
                    classes="story-header",
                )
            )
            for task in unassigned:
                container.mount(TaskRow(task))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new-story":
            self.app.show_story_form()  # type: ignore[attr-defined]
        elif event.button.id == "btn-new-task":
            self.app.show_task_form()  # type: ignore[attr-defined]

    def on_static_click(self, event: Static.Click) -> None:
        """Handle clicks on story headers (collapse/expand) and task rows (edit)."""
        widget = event.static
        if isinstance(widget, StoryHeader):
            expanded = widget.toggle()
            story_id = widget.story.id
            for row in self.query(".task-row"):
                if isinstance(row, TaskRow) and row.task_data.story_id == story_id:
                    row.display = expanded
        elif isinstance(widget, TaskRow):
            self.app.show_task_form(task=widget.task_data)  # type: ignore[attr-defined]
