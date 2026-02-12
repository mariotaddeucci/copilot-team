from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.tui.screens.chat import ChatScreen
from copilot_team.tui.screens.story_form import StoryFormScreen
from copilot_team.tui.screens.task_form import TaskFormScreen
from copilot_team.tui.screens.tree_view import TreeViewScreen


class CopilotTeamApp(App):
    """A TUI for managing stories and tasks."""

    TITLE = "Copilot Team"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("t", "show_tree", "Tree View"),
        Binding("s", "new_story", "New Story"),
        Binding("a", "new_task", "New Task"),
        Binding("c", "show_chat", "Chat"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, task_store: BaseTaskStoreBackend) -> None:
        super().__init__()
        self.task_store = task_store

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen(TreeViewScreen())

    def action_show_tree(self) -> None:
        self.switch_screen(TreeViewScreen())

    def action_new_story(self) -> None:
        self.push_screen(StoryFormScreen())

    def action_new_task(self) -> None:
        self.push_screen(TaskFormScreen())

    def action_show_chat(self) -> None:
        self.switch_screen(ChatScreen())
