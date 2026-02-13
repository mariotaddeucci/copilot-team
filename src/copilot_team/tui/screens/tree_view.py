from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Tree

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task


class TreeViewPanel(Vertical):
    """Panel showing a tree view of stories and their tasks."""

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
        tree: Tree[Story | Task] = Tree("Stories", id="stories-tree")
        tree.root.expand()
        tree.show_root = False
        yield tree

    def on_mount(self) -> None:
        self._refresh_tree()

    def _status_icon(self, status: str) -> str:
        icons = {
            "created": "⬜",
            "planning": "📝",
            "ready": "🟡",
            "in_progress": "🔵",
            "completed": "✅",
        }
        return icons.get(status, "❓")

    def _status_color(self, status: str) -> str:
        colors = {
            "created": "#6272a4",
            "planning": "#f1fa8c",
            "ready": "#ffb86c",
            "in_progress": "#8be9fd",
            "completed": "#50fa7b",
        }
        return colors.get(status, "#f8f8f2")

    def _refresh_tree(self) -> None:
        tree = self.query_one("#stories-tree", Tree)
        tree.clear()

        stories = self.task_store.list_stories()
        stories.sort()

        for story in stories:
            icon = self._status_icon(story.status)
            color = self._status_color(story.status)
            label = f"{icon} [{color}]{story.name}[/] [dim]— {story.description}[/] [{color}]{story.status}[/]"
            story_node = tree.root.add(label, data=story)

            tasks = self.task_store.list_tasks(story_id=story.id)
            tasks.sort()
            for task in tasks:
                task_icon = self._status_icon(task.status)
                task_color = self._status_color(task.status)
                checklist_total = len(task.checklist)
                checklist_done = sum(1 for item in task.checklist if item.completed)
                checklist_info = (
                    f"[#bd93f9][{checklist_done}/{checklist_total}][/]"
                    if checklist_total > 0
                    else ""
                )
                task_label = f"{task_icon} [{task_color}]{task.name}[/] {checklist_info} [{task_color}]{task.status}[/]"
                story_node.add_leaf(task_label, data=task)

            story_node.expand()

        tree.root.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected[Story | Task]) -> None:
        node_data = event.node.data
        if isinstance(node_data, Story):
            self.app.show_story_form(story=node_data)  # type: ignore[attr-defined]
        elif isinstance(node_data, Task):
            self.app.show_task_form(task=node_data)  # type: ignore[attr-defined]
