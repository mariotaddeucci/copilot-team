from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Static, Tree

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task


class TreeViewScreen(Screen):
    """Screen showing a tree view of stories and their tasks."""

    BINDINGS = [
        ("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Stories & Tasks", id="tree-title")
        tree: Tree[Story | Task] = Tree("📋 Stories", id="stories-tree")
        tree.root.expand()
        yield tree
        with Static(id="tree-buttons"):
            yield Button("New Story [s]", id="btn-new-story", variant="primary")
            yield Button("New Task [a]", id="btn-new-task", variant="success")
            yield Button("Chat [c]", id="btn-chat", variant="default")
            yield Button("Refresh [r]", id="btn-refresh", variant="default")

    @property
    def task_store(self) -> BaseTaskStoreBackend:
        return self.app.task_store  # type: ignore[attr-defined]

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

    def _refresh_tree(self) -> None:
        tree = self.query_one("#stories-tree", Tree)
        tree.clear()

        stories = self.task_store.list_stories()
        stories.sort()

        for story in stories:
            icon = self._status_icon(story.status)
            label = f"{icon} {story.name} - {story.description} [{story.status}]"
            story_node = tree.root.add(label, data=story)

            tasks = self.task_store.list_tasks(story_id=story.id)
            tasks.sort()
            for task in tasks:
                task_icon = self._status_icon(task.status)
                checklist_total = len(task.checklist)
                checklist_done = sum(1 for item in task.checklist if item.completed)
                checklist_info = (
                    f"[{checklist_done}/{checklist_total}]"
                    if checklist_total > 0
                    else ""
                )
                task_label = (
                    f"{task_icon} {task.name} {checklist_info} [{task.status}]"
                )
                story_node.add_leaf(task_label, data=task)

            story_node.expand()

        tree.root.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected[Story | Task]) -> None:
        node_data = event.node.data
        if isinstance(node_data, Story):
            from copilot_team.tui.screens.story_form import StoryFormScreen

            self.app.push_screen(StoryFormScreen(story=node_data))
        elif isinstance(node_data, Task):
            from copilot_team.tui.screens.task_form import TaskFormScreen

            self.app.push_screen(TaskFormScreen(task=node_data))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new-story":
            self.app.action_new_story()  # type: ignore[attr-defined]
        elif event.button.id == "btn-new-task":
            self.app.action_new_task()  # type: ignore[attr-defined]
        elif event.button.id == "btn-chat":
            self.app.action_show_chat()  # type: ignore[attr-defined]
        elif event.button.id == "btn-refresh":
            self._refresh_tree()

    def action_refresh(self) -> None:
        self._refresh_tree()
