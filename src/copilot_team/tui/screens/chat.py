from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Select, Static

if TYPE_CHECKING:
    from copilot import CopilotClient

AVAILABLE_MODELS = [
    ("Auto", "auto"),
    ("GPT-4o", "gpt-4o"),
    ("GPT-4.1", "gpt-4.1"),
    ("Claude Sonnet 4", "claude-sonnet-4"),
    ("o3-mini", "o3-mini"),
]


class ChatPanel(Vertical):
    """Chat interface with Copilot SDK session management and model switching."""

    DEFAULT_CSS = """
    ChatPanel {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._session = None
        self._processing = False

    @property
    def _copilot_client(self) -> CopilotClient:
        return self.app.copilot_client  # type: ignore[attr-defined]

    @property
    def _task_service(self):
        return self.app.task_service  # type: ignore[attr-defined]

    @property
    def _settings(self):
        return self.app.settings  # type: ignore[attr-defined]

    def compose(self) -> ComposeResult:
        with Horizontal(id="chat-toolbar"):
            yield Select(
                AVAILABLE_MODELS,
                value="auto",
                allow_blank=False,
                id="chat-model-select",
            )
            yield Button("New Session", id="chat-new-session", variant="success")
            yield Button("Recreate Session", id="chat-recreate-session", variant="default")
        yield RichLog(id="chat-log", markup=True)
        with Horizontal(id="chat-input-bar"):
            yield Input(
                placeholder="Type a message...",
                id="chat-input",
            )
            yield Button("Send", id="chat-send", variant="primary")

    def on_mount(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        log.write("[dim]Chat ready. Send a message to start a session.[/dim]")
        # Set default model from settings
        default_model = self._settings.chat.default_model
        model_select = self.query_one("#chat-model-select", Select)
        model_select.value = default_model

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "chat-send":
            self._send_message()
        elif event.button.id == "chat-new-session":
            self._start_new_session()
        elif event.button.id == "chat-recreate-session":
            self._recreate_session()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "chat-input":
            self._send_message()

    def _get_selected_model(self) -> str | None:
        model_select = self.query_one("#chat-model-select", Select)
        value = model_select.value
        if value == "auto" or value == Select.BLANK:
            return None
        return str(value)

    def _send_message(self) -> None:
        input_widget = self.query_one("#chat-input", Input)
        message = input_widget.value.strip()
        if not message:
            return
        if self._processing:
            self.app.notify("Please wait for the current response.", severity="warning")
            return
        input_widget.value = ""
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[bold cyan]You:[/bold cyan] {message}")
        self.run_worker(self._async_send(message), exclusive=True)

    async def _async_send(self, message: str) -> None:
        self._processing = True
        log = self.query_one("#chat-log", RichLog)
        try:
            if self._session is None:
                await self._ensure_session()
            done = asyncio.Event()
            response_parts: list[str] = []

            def handler(event):
                if event.type == "assistant.message.delta":
                    response_parts.append(event.data.delta_content)
                elif event.type == "assistant.message":
                    response_parts.clear()
                    response_parts.append(event.data.content)
                elif event.type == "session.idle":
                    done.set()
                elif event.type == "session.error":
                    response_parts.append(f"[red]Error: {event.data.message}[/red]")
                    done.set()

            unsubscribe = self._session.on(handler)
            try:
                await self._session.send({"prompt": message})
                await asyncio.wait_for(done.wait(), timeout=120.0)
            except asyncio.TimeoutError:
                log.write("[yellow]Response timed out.[/yellow]")
            finally:
                unsubscribe()

            if response_parts:
                full = "".join(response_parts)
                log.write(f"[bold green]Assistant:[/bold green] {full}")
            else:
                log.write("[dim]No response received.[/dim]")
        except Exception as exc:
            log.write(f"[red]Error: {exc}[/red]")
        finally:
            self._processing = False

    async def _ensure_session(self) -> None:
        from copilot_team.tui.chat_tools import build_task_tools

        model = self._get_selected_model()
        config: dict = {
            "tools": build_task_tools(self._task_service),
        }
        if model:
            config["model"] = model
        self._session = await self._copilot_client.create_session(config)
        log = self.query_one("#chat-log", RichLog)
        log.write(f"[dim]Session created (model={model or 'auto'}).[/dim]")

    def _start_new_session(self) -> None:
        self.run_worker(self._async_new_session(), exclusive=True)

    async def _async_new_session(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        if self._session is not None:
            try:
                await self._session.destroy()
            except Exception:
                pass
            self._session = None
        await self._ensure_session()
        log.write("[dim]New session started.[/dim]")

    def _recreate_session(self) -> None:
        self.run_worker(self._async_recreate_session(), exclusive=True)

    async def _async_recreate_session(self) -> None:
        log = self.query_one("#chat-log", RichLog)
        if self._session is not None:
            try:
                await self._session.destroy()
            except Exception:
                pass
            self._session = None
        log.clear()
        log.write("[dim]Session recreated. Chat history cleared.[/dim]")
        await self._ensure_session()
