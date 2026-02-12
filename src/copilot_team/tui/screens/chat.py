from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, RichLog, Static


class ChatScreen(Screen):
    """Chat interface screen for future AI agent interaction."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="chat-container"):
            yield Static("[bold]💬 Chat[/bold] (future AI agent interaction)")
            yield RichLog(id="chat-log", markup=True)
            with Static(id="chat-input-bar"):
                yield Input(
                    placeholder="Type a message...",
                    id="chat-input",
                )
                yield Button("Send", id="chat-send", variant="primary")

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write("[dim]Chat interface ready. AI agent integration coming soon.[/dim]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "chat-send":
            self._send_message()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            self._send_message()

    def _send_message(self) -> None:
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value.strip()
        if not message:
            return

        log = self.query_one("#chat-log", RichLog)
        log.write(f"[bold cyan]You:[/bold cyan] {message}")
        log.write(
            "[dim italic]AI agent integration coming soon...[/dim italic]"
        )
        input_widget.value = ""

    def action_go_back(self) -> None:
        self.app.pop_screen()
