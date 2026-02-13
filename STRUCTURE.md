# Project Structure

```
copilot-team/
├── pyproject.toml                          # Project config, dependencies, tool settings
├── STRUCTURE.md                            # This file
├── src/
│   ├── config.toml                         # Application settings (DB path, log level, etc.)
│   └── copilot_team/
│       ├── __init__.py
│       ├── main.py                         # Entry point — creates injector, wires deps, runs TUI
│       │
│       ├── core/                           # Business logic & domain layer (no UI deps)
│       │   ├── dependencies.py             # Injector module — binds interfaces to implementations
│       │   ├── exceptions.py               # Custom domain exceptions
│       │   ├── interfaces.py               # Abstract base classes (BaseTaskStoreBackend)
│       │   ├── models.py                   # Pydantic domain models (Story, Task, TaskChecklistItem)
│       │   ├── services.py                 # Service layer (TaskService, ChatService)
│       │   └── settings.py                 # Typed settings loaded from config.toml
│       │
│       ├── backends/                       # Storage implementations
│       │   ├── __init__.py
│       │   └── sqlite_task_store_backend.py  # SQLite backend for BaseTaskStoreBackend
│       │
│       ├── agents/                         # Background agents and tool adapters
│       │   ├── __init__.py
│       │   ├── tools/                     # Copilot SDK tool definitions (adapter layer)
│       │   │   ├── __init__.py
│       │   │   └── chat_tools.py          # Thin wrappers exposing TaskService to the LLM
│       │   └── worker/
│       │       ├── __init__.py
│       │       └── repository_manager.py  # Git repository & worktree management
│       │
│       └── tui/                            # Terminal UI (Textual) — presentation only
│           ├── __init__.py
│           ├── app.py                      # CopilotTeamApp — top-level app, navigation handler
│           ├── messages.py                 # Custom Textual messages for navigation
│           ├── pydantic_form.py            # Auto-generated form builder from Pydantic models
│           ├── styles.tcss                 # Monokai theme stylesheet
│           └── screens/
│               ├── __init__.py
│               ├── chat.py                 # ChatPanel — Copilot SDK chat interface
│               ├── settings.py             # SettingsPanel — app settings editor
│               ├── story_form.py           # StoryFormPanel — create/edit story
│               ├── task_form.py            # TaskFormPanel — create/edit task
│               └── tree_view.py            # TreeViewPanel — collapsible story/task tree
│
└── tests/
    ├── __init__.py
    ├── conftest.py                         # Shared fixtures (InMemoryTaskStoreBackend)
    ├── test_chat_tools.py                  # Tests for Copilot SDK tool definitions
    ├── test_pydantic_form.py               # Tests for the form builder
    ├── test_services.py                    # Tests for TaskService / ChatService
    └── test_tui.py                         # Integration tests for the TUI screens
```

## Architecture

### Dependency Injection

All major services are wired via the `injector` library:

| Interface / Class        | Binding                              | Scope     |
|--------------------------|--------------------------------------|-----------|
| `Settings`               | Auto-created from `config.toml`      | Singleton |
| `logging.Logger`         | `create_logger(Inject[Settings])`    | Singleton |
| `CopilotClient`          | Auto-start config                    | Singleton |
| `BaseTaskStoreBackend`   | Loaded from `settings.core.implementations.task_store` | Singleton |
| `TaskService`            | Auto-injected with `BaseTaskStoreBackend` | Singleton |

Classes that participate in DI use `Inject[T]` type annotations on their constructors
(e.g. `RepositoryManager.__init__(self, settings: Inject[Settings])`).

### Layer Separation

| Layer       | Directory          | Depends On        | Description |
|-------------|--------------------|-------------------|-------------|
| **Core**    | `core/`            | —                 | Pure business logic, models, interfaces |
| **Backends**| `backends/`        | `core`            | Storage implementations |
| **Agents**  | `agents/`          | `core`            | Background workers and tool adapters |
| **Tools**   | `agents/tools/`    | `core`            | Copilot SDK adapters (thin wrappers) |
| **TUI**     | `tui/`             | `core`, `agents`  | Presentation layer (Textual widgets) |

Screens receive dependencies via constructor injection. Navigation between
screens is handled through Textual message passing (`NavigateToTree`,
`NavigateToStoryForm`, `NavigateToTaskForm`) — screens never call
`self.app.method()` directly.
