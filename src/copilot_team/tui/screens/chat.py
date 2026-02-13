from __future__ import annotations

import asyncio
from typing import Any

from copilot import CopilotClient
from copilot.types import SessionConfig
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Select

from copilot_team.core.services import ChatService, TaskService
from copilot_team.core.settings import Settings

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

    def __init__(
        self,
        task_service: TaskService,
        copilot_client: CopilotClient,
        settings: Settings,
    ) -> None:
        super().__init__()
        self._task_service = task_service
        self._copilot_client = copilot_client
        self._settings = settings
        self._session: Any | None = None
        self._chat_service = ChatService()

    def compose(self) -> ComposeResult:
        with Horizontal(id="chat-toolbar"):
            yield Select(
                AVAILABLE_MODELS,
                value="auto",
                allow_blank=False,
                id="chat-model-select",
            )
            yield Button("New Session", id="chat-new-session", variant="success")
            yield Button(
                "Recreate Session", id="chat-recreate-session", variant="default"
            )
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
        input_widget.value = ""
        log = self.query_one("#chat-log", RichLog)
        enqueued = self._chat_service.enqueue_message(message)
        status = " [dim](enqueue)[/dim]" if enqueued else ""
        log.write(f"[bold cyan]You{status}:[/bold cyan] {message}")
        if not self._chat_service.is_processing:
            self.run_worker(self._async_process_queue(), exclusive=True)

    async def _async_process_queue(self) -> None:
        self._chat_service.set_processing(True)
        try:
            while message := self._chat_service.next_message():
                await self._async_send(message)
        finally:
            self._chat_service.set_processing(False)

    async def _async_send(self, message: str) -> None:
        log = self.query_one("#chat-log", RichLog)
        try:
            if self._session is None:
                await self._ensure_session()
            session = self._session
            if session is None:
                raise RuntimeError("Failed to create chat session.")
            done = asyncio.Event()
            response_parts: list[str] = []
            received_delta = False
            wrote_assistant_label = False

            def handler(event: Any) -> None:
                nonlocal received_delta, wrote_assistant_label
                if event.type == "assistant.message.delta":
                    response_parts.append(event.data.delta_content)
                    if event.data.delta_content:
                        received_delta = True
                        if not wrote_assistant_label:
                            log.write(
                                f"[bold green]Assistant:[/bold green] {event.data.delta_content}"
                            )
                            wrote_assistant_label = True
                        else:
                            log.write(event.data.delta_content)
                elif event.type == "assistant.message":
                    response_parts.clear()
                    response_parts.append(event.data.content)
                elif event.type == "session.idle":
                    done.set()
                elif event.type == "session.error":
                    response_parts.append(f"[red]Error: {event.data.message}[/red]")
                    done.set()

            unsubscribe = session.on(handler)
            try:
                await session.send({"prompt": message, "mode": "enqueue"})
                await asyncio.wait_for(done.wait(), timeout=120.0)
            except asyncio.TimeoutError:
                log.write("[yellow]Response timed out.[/yellow]")
            finally:
                unsubscribe()

            if not response_parts:
                log.write("[dim]No response received.[/dim]")
                return

            full = "".join(response_parts)
            if not full:
                log.write("[dim]No response received.[/dim]")
            elif not received_delta:
                log.write(f"[bold green]Assistant:[/bold green] {full}")
        except Exception as exc:
            log.write(f"[red]Error: {exc}[/red]")

    async def _ensure_session(self) -> None:
        from copilot_team.agents.tools.chat_tools import build_task_tools

        model = self._get_selected_model()
        config = SessionConfig(tools=build_task_tools(self._task_service))
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
