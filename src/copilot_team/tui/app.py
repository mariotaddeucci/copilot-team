from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Static

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.tui.screens.chat import ChatPanel
from copilot_team.tui.screens.story_form import StoryFormPanel
from copilot_team.tui.screens.task_form import TaskFormPanel
from copilot_team.tui.screens.tree_view import TreeViewPanel


class Sidebar(Vertical):
    """Left sidebar with menu and activity section."""

    def compose(self) -> ComposeResult:
        yield Static("🤖 [bold]Copilot Team[/bold]", id="sidebar-title")
        with Vertical(id="sidebar-menu"):
            yield Static("📋  Stories & Tasks", id="menu-tree", classes="menu-item")
            yield Static("📝  New Story", id="menu-story", classes="menu-item")
            yield Static("✏️  New Task", id="menu-task", classes="menu-item")
            yield Static("💬  Chat", id="menu-chat", classes="menu-item")
        with Vertical(id="sidebar-activity"):
            yield Static("[bold]⚡ Activity[/bold]", id="activity-title")
            yield Static(
                "[dim]No background tasks running[/dim]", id="activity-content"
            )


class CopilotTeamApp(App):
    """A TUI for managing stories and tasks."""

    TITLE = "Copilot Team"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("t", "show_tree", "Tree View", show=True),
        Binding("s", "new_story", "New Story", show=True),
        Binding("a", "new_task", "New Task", show=True),
        Binding("c", "show_chat", "Chat", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, task_store: BaseTaskStoreBackend) -> None:
        super().__init__()
        self.task_store = task_store

    def compose(self) -> ComposeResult:
        with Horizontal(id="app-layout"):
            yield Sidebar(id="sidebar")
            with Vertical(id="main-area"):
                yield Static("📋 Stories & Tasks", id="page-title")
                yield Container(id="content-area")
        yield Footer()

    def on_mount(self) -> None:
        self._show_panel(TreeViewPanel())

    def _show_panel(self, panel: Widget, title: str = "") -> None:
        content = self.query_one("#content-area", Container)
        content.remove_children()
        content.mount(panel)
        if title:
            self.query_one("#page-title", Static).update(title)

    def _update_active_menu(self, active_id: str) -> None:
        for item in self.query(".menu-item"):
            item.remove_class("active")
        try:
            self.query_one(f"#{active_id}").add_class("active")
        except Exception:
            pass

    def action_show_tree(self) -> None:
        self._update_active_menu("menu-tree")
        self.query_one("#page-title", Static).update("📋 Stories & Tasks")
        self._show_panel(TreeViewPanel())

    def action_new_story(self) -> None:
        self._update_active_menu("menu-story")
        self.query_one("#page-title", Static).update("📝 New Story")
        self._show_panel(StoryFormPanel())

    def action_new_task(self) -> None:
        self._update_active_menu("menu-task")
        self.query_one("#page-title", Static).update("✏️  New Task")
        self._show_panel(TaskFormPanel())

    def action_show_chat(self) -> None:
        self._update_active_menu("menu-chat")
        self.query_one("#page-title", Static).update("💬 Chat")
        self._show_panel(ChatPanel())

    def show_story_form(self, story=None) -> None:
        title = "📝 Edit Story" if story else "📝 New Story"
        self._update_active_menu("menu-story")
        self.query_one("#page-title", Static).update(title)
        self._show_panel(StoryFormPanel(story=story))

    def show_task_form(self, task=None) -> None:
        title = "✏️  Edit Task" if task else "✏️  New Task"
        self._update_active_menu("menu-task")
        self.query_one("#page-title", Static).update(title)
        self._show_panel(TaskFormPanel(task=task))

    def on_click(self, event) -> None:
        widget = event.widget
        if hasattr(widget, "id") and widget.id:
            if widget.id == "menu-tree":
                self.action_show_tree()
            elif widget.id == "menu-story":
                self.action_new_story()
            elif widget.id == "menu-task":
                self.action_new_task()
            elif widget.id == "menu-chat":
                self.action_show_chat()
