from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, Select, Static

from copilot_team.core.settings import Settings
from copilot_team.tui.messages import NavigateToTree

AVAILABLE_MODELS = [
    ("Auto", "auto"),
    ("GPT-4o", "gpt-4o"),
    ("GPT-4.1", "gpt-4.1"),
    ("Claude Sonnet 4", "claude-sonnet-4"),
    ("o3-mini", "o3-mini"),
]


class SettingsPanel(Vertical):
    """Settings screen with Chat and Copilot tabs."""

    DEFAULT_CSS = """
    SettingsPanel {
        height: 1fr;
        width: 1fr;
        padding: 1 2;
    }
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._active_tab = "chat"

    def compose(self) -> ComposeResult:
        yield Static("[bold] Settings[/bold]", id="settings-title")
        with Horizontal(id="settings-tabs"):
            yield Button("Chat", id="settings-tab-chat", variant="primary")
            yield Button("Copilot", id="settings-tab-copilot", variant="default")
        yield Vertical(id="settings-content")

    def on_mount(self) -> None:
        self._show_chat_tab()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id == "settings-tab-chat":
            self._active_tab = "chat"
            self._update_tab_styles()
            self._show_chat_tab()
        elif btn_id == "settings-tab-copilot":
            self._active_tab = "copilot"
            self._update_tab_styles()
            self._show_copilot_tab()
        elif btn_id == "settings-save":
            self._save_settings()
        elif btn_id == "settings-back":
            self.post_message(NavigateToTree())

    def _update_tab_styles(self) -> None:
        chat_btn = self.query_one("#settings-tab-chat", Button)
        copilot_btn = self.query_one("#settings-tab-copilot", Button)
        if self._active_tab == "chat":
            chat_btn.variant = "primary"
            copilot_btn.variant = "default"
        else:
            chat_btn.variant = "default"
            copilot_btn.variant = "primary"

    def _show_chat_tab(self) -> None:
        content = self.query_one("#settings-content", Vertical)
        content.remove_children()
        content.mount(Label("Default Model:"))
        content.mount(
            Select(
                AVAILABLE_MODELS,
                value=self._settings.chat.default_model,
                allow_blank=False,
                id="settings-chat-model",
            )
        )
        buttons = Static(classes="form-buttons")
        content.mount(buttons)
        buttons.mount(Button("Save", id="settings-save", variant="primary"))
        buttons.mount(Button("Back", id="settings-back", variant="error"))

    def _show_copilot_tab(self) -> None:
        content = self.query_one("#settings-content", Vertical)
        content.remove_children()
        content.mount(Label("Max Chat Sessions:"))
        content.mount(
            Input(
                value=str(self._settings.copilot.max_chat_sessions),
                id="settings-copilot-max-chat",
                placeholder="Max concurrent chat sessions",
            )
        )
        content.mount(Label("Max Background Agents:"))
        content.mount(
            Input(
                value=str(self._settings.copilot.max_background_agents),
                id="settings-copilot-max-agents",
                placeholder="Max concurrent background agents",
            )
        )
        buttons = Static(classes="form-buttons")
        content.mount(buttons)
        buttons.mount(Button("Save", id="settings-save", variant="primary"))
        buttons.mount(Button("Back", id="settings-back", variant="error"))

    def _save_settings(self) -> None:
        try:
            if self._active_tab == "chat":
                model_select = self.query_one("#settings-chat-model", Select)
                value = model_select.value
                if value != Select.BLANK:
                    self._settings.chat.default_model = str(value)
            elif self._active_tab == "copilot":
                max_chat = self.query_one("#settings-copilot-max-chat", Input)
                max_agents = self.query_one("#settings-copilot-max-agents", Input)
                self._settings.copilot.max_chat_sessions = int(max_chat.value)
                self._settings.copilot.max_background_agents = int(max_agents.value)
            self.app.notify("Settings saved!", severity="information")
        except (ValueError, TypeError) as exc:
            self.app.notify(f"Invalid value: {exc}", severity="error")
