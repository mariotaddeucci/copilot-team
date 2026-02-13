from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task


def _status_icon(status: str) -> str:
    icons = {
        "pending": "○",
        "planning": "◎",
        "ready": "●",
        "in_progress": "▸",
        "completed": "✓",
    }
    return icons.get(status, "?")


def _status_color(status: str) -> str:
    colors = {
        "pending": "#75715E",
        "planning": "#E6DB74",
        "ready": "#FD971F",
        "in_progress": "#66D9EF",
        "completed": "#A6E22E",
    }
    return colors.get(status, "#F8F8F2")


# Column widths for tabular alignment
COL_NAME = 30
COL_AGENT = 14
COL_REPO = 18
COL_CHECK = 8
# Story header prefix: "  ▾ ● " = 6 visible chars + spaces
STORY_PREFIX_LEN = 6
# Task tree prefix: " ├─ ●  " = 7 visible chars + spaces
TASK_PREFIX_LEN = 9
# Checklist tree prefix: " │  ├─ ✓  " = deeper indent
CHECK_PREFIX_LEN = 12


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
        arrow = "▾" if self._expanded else "▸"
        name = self._story.name
        desc = self._story.description or ""
        name_col = f"{name}  — {desc}" if desc else name
        status = self._story.status
        remaining = COL_NAME + COL_AGENT + COL_REPO + COL_CHECK - STORY_PREFIX_LEN
        return (
            f" [{color}]{arrow} {icon}[/]  "
            f"[bold]{name_col:<{remaining}s}[/]"
            f"[{color}]{status}[/]"
        )

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
    """A single task row in the tree."""

    def __init__(self, task: Task, is_last: bool = False) -> None:
        self._data = task
        self._is_last = is_last
        self._expanded = False
        super().__init__(self._render_label(), classes="task-row")
        self.id = f"task-row-{task.id}"

    def _render_label(self) -> str:
        icon = _status_icon(self._data.status)
        color = _status_color(self._data.status)
        connector = " └─" if self._is_last else " ├─"
        name = self._data.name
        agent = self._data.agent or "-"
        repo = self._data.repository_name or "-"
        total = len(self._data.checklist)
        done = sum(1 for c in self._data.checklist if c.completed)
        check = f"{done}/{total}" if total else "-"
        status = self._data.status
        has_checklist = bool(self._data.checklist)
        arrow = ""
        if has_checklist:
            arrow = " ▾" if self._expanded else " ▸"
        name_w = COL_NAME - TASK_PREFIX_LEN + STORY_PREFIX_LEN
        return (
            f" [#75715E]{connector}[/] [{color}]{icon}[/]{arrow} "
            f"[{color}]{name:<{name_w}s}[/]"
            f"[dim]{agent:<{COL_AGENT}s}[/]"
            f"[dim]{repo:<{COL_REPO}s}[/]"
            f"[#AE81FF]{check:<{COL_CHECK}s}[/]"
            f"[{color}]{status}[/]"
        )

    def toggle_checklist(self) -> bool:
        self._expanded = not self._expanded
        self.update(self._render_label())
        return self._expanded

    def collapse_checklist(self) -> None:
        if self._expanded:
            self._expanded = False
            self.update(self._render_label())

    @property
    def task_data(self) -> Task:
        return self._data

    @property
    def expanded(self) -> bool:
        return self._expanded


class ChecklistRow(Static):
    """A single checklist item row (third level) in the tree."""

    def __init__(
        self, description: str, completed: bool, is_last_check: bool,
        parent_is_last_task: bool,
    ) -> None:
        self._description = description
        self._completed = completed
        label = self._render_label(is_last_check, parent_is_last_task)
        super().__init__(label, classes="checklist-tree-row")

    def _render_label(self, is_last_check: bool, parent_is_last: bool) -> str:
        pipe = " " if parent_is_last else " │"
        connector = " └─" if is_last_check else " ├─"
        if self._completed:
            icon = "✓"
            color = "#A6E22E"
            status = "complete"
        else:
            icon = "○"
            color = "#75715E"
            status = "pending"
        return (
            f" [#75715E]{pipe} {connector}[/] [{color}]{icon}[/]  "
            f"[{color}]{self._description}[/]"
            f"  [{color}]{status}[/]"
        )


class TreeViewPanel(Vertical):
    """Panel showing stories and tasks in a clean collapsible layout."""

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
            yield Static("", id="tree-spacer")
            yield Button("+ Story", id="btn-new-story", variant="default")
            yield Button("+ Task", id="btn-new-task", variant="default")
        yield Static(self._header_row(), id="table-header")
        yield VerticalScroll(id="stories-tree")

    def _header_row(self) -> str:
        offset = STORY_PREFIX_LEN + 2
        return (
            f"  [bold #AE81FF]{'Name':<{COL_NAME + offset - 2}s}"
            f"{'Agent':<{COL_AGENT}s}"
            f"{'Repository':<{COL_REPO}s}"
            f"{'Check':<{COL_CHECK}s}"
            f"{'Status'}[/]"
        )

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
            for i, task in enumerate(tasks):
                is_last = i == len(tasks) - 1
                container.mount(TaskRow(task, is_last=is_last))

        # Unassigned tasks section
        unassigned = [
            t for t in self.task_store.list_tasks() if t.story_id is None
        ]
        if unassigned:
            unassigned.sort()
            container.mount(
                Static(
                    " [#FD971F]▾ ○[/]  [bold #FD971F]Unassigned[/]",
                    id="unassigned-header",
                    classes="story-header",
                )
            )
            for i, task in enumerate(unassigned):
                is_last = i == len(unassigned) - 1
                container.mount(TaskRow(task, is_last=is_last))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new-story":
            self.app.show_story_form()  # type: ignore[attr-defined]
        elif event.button.id == "btn-new-task":
            self.app.show_task_form()  # type: ignore[attr-defined]

    def on_static_click(self, event: Static.Click) -> None:
        """Handle clicks on story headers, task rows, and checklist expansion."""
        widget = event.static
        if isinstance(widget, StoryHeader):
            expanded = widget.toggle()
            story_id = widget.story.id
            task_ids = set()
            for row in self.query(".task-row"):
                if isinstance(row, TaskRow) and row.task_data.story_id == story_id:
                    row.display = expanded
                    task_ids.add(row.task_data.id)
            for chk in self.query(".checklist-tree-row"):
                if any(
                    chk.id and chk.id.startswith(f"chk-tree-{tid}-")
                    for tid in task_ids
                ):
                    chk.display = False
            # Reset expanded state on tasks when collapsing
            if not expanded:
                for row in self.query(".task-row"):
                    if isinstance(row, TaskRow) and row.task_data.story_id == story_id:
                        row.collapse_checklist()
        elif isinstance(widget, TaskRow):
            task = widget.task_data
            if task.checklist:
                expanded = widget.toggle_checklist()
                self._toggle_checklist_rows(widget, expanded)
            else:
                self.app.show_task_form(task=task)  # type: ignore[attr-defined]

    def _toggle_checklist_rows(self, task_row: TaskRow, show: bool) -> None:
        container = self.query_one("#stories-tree", VerticalScroll)
        task_id = task_row.task_data.id
        existing = [
            w for w in container.query(".checklist-tree-row")
            if w.id and w.id.startswith(f"chk-tree-{task_id}-")
        ]
        if show and not existing:
            items = task_row.task_data.checklist
            widgets_to_mount = []
            for j, item in enumerate(items):
                is_last_check = j == len(items) - 1
                chk_row = ChecklistRow(
                    description=item.description,
                    completed=item.completed,
                    is_last_check=is_last_check,
                    parent_is_last_task=task_row._is_last,
                )
                chk_row.id = f"chk-tree-{task_id}-{j}"
                widgets_to_mount.append(chk_row)
            container.mount_all(widgets_to_mount, after=task_row)
        elif show:
            for w in existing:
                w.display = True
        else:
            for w in existing:
                w.display = False
