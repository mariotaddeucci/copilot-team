from copilot import CopilotClient
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Static

from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.settings import Settings
from copilot_team.tui.screens.chat import ChatPanel
from copilot_team.tui.screens.settings import SettingsPanel
from copilot_team.tui.screens.story_form import StoryFormPanel
from copilot_team.tui.screens.task_form import TaskFormPanel
from copilot_team.tui.screens.tree_view import TreeViewPanel


class Sidebar(Vertical):
    """Left sidebar with menu and activity section."""

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar-menu"):
            yield Static(
                "  [bold]Tasks[/bold]", id="menu-tree", classes="menu-item active"
            )
            yield Static(
                "  [bold]Chat[/bold]", id="menu-chat", classes="menu-item"
            )
            yield Static(
                "  [bold]Settings[/bold]", id="menu-settings", classes="menu-item"
            )
        with Vertical(id="sidebar-activity"):
            yield Static("[bold] Activity[/bold]", id="activity-title")
            yield Static(
                "[dim]No background tasks[/dim]", id="activity-content"
            )


class CopilotTeamApp(App):
    """A TUI for managing stories and tasks."""

    TITLE = "Copilot Team"
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("t", "show_tree", "Tasks", show=True),
        Binding("c", "show_chat", "Chat", show=True),
        Binding("s", "show_settings", "Settings", show=True),
        Binding("n", "new_task", "New Task", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    def __init__(
        self,
        task_store: BaseTaskStoreBackend,
        copilot_client: CopilotClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        super().__init__()
        self.task_store = task_store
        self.copilot_client = copilot_client or CopilotClient(
            {"auto_restart": True, "auto_start": True}
        )
        self.settings = settings or Settings()
        self._ctrl_c_count = 0

    def compose(self) -> ComposeResult:
        with Horizontal(id="app-layout"):
            yield Sidebar(id="sidebar")
            yield Container(id="content-area")
        yield Footer()

    def on_mount(self) -> None:
        self._show_panel(TreeViewPanel())

    def _show_panel(self, panel: Widget) -> None:
        """Replace the content area with the given panel."""
        content = self.query_one("#content-area", Container)
        content.remove_children()
        content.mount(panel)

    def _update_active_menu(self, active_id: str) -> None:
        """Highlight the active menu item in the sidebar."""
        from textual.css.query import NoMatches

        for item in self.query(".menu-item"):
            item.remove_class("active")
        try:
            self.query_one(f"#{active_id}").add_class("active")
        except NoMatches:
            pass

    def action_show_tree(self) -> None:
        self._update_active_menu("menu-tree")
        self._show_panel(TreeViewPanel())

    def action_show_chat(self) -> None:
        self._update_active_menu("menu-chat")
        self._show_panel(ChatPanel())

    def action_show_settings(self) -> None:
        self._update_active_menu("menu-settings")
        self._show_panel(SettingsPanel())

    def action_new_task(self) -> None:
        self.show_task_form()

    def show_story_form(self, story=None) -> None:
        """Navigate to story form for create/edit."""
        self._update_active_menu("menu-tree")
        self._show_panel(StoryFormPanel(story=story))

    def show_task_form(self, task=None, story_id=None) -> None:
        """Navigate to task form for create/edit."""
        self._update_active_menu("menu-tree")
        self._show_panel(TaskFormPanel(task=task, story_id=story_id))

    def on_click(self, event) -> None:
        """Handle sidebar menu item clicks and dispatch to navigation actions."""
        widget = event.widget
        if hasattr(widget, "id") and widget.id:
            if widget.id == "menu-tree":
                self.action_show_tree()
            elif widget.id == "menu-chat":
                self.action_show_chat()
            elif widget.id == "menu-settings":
                self.action_show_settings()

    async def on_key(self, event) -> None:
        """Handle Ctrl+C double-press to quit."""
        if event.key == "ctrl+c":
            self._ctrl_c_count += 1
            if self._ctrl_c_count >= 2:
                self.exit()
            else:
                self.notify("Press Ctrl+C again to quit", severity="warning")
                self.set_timer(1.5, self._reset_ctrl_c)
            event.prevent_default()

    def _reset_ctrl_c(self) -> None:
        self._ctrl_c_count = 0
