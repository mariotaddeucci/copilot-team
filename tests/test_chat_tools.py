"""Tests for chat_tools — the Copilot SDK tool definitions backed by TaskService."""

import inspect

import pytest

from copilot.types import Tool, ToolInvocation, ToolResult

from copilot_team.core.models import Story, Task
from copilot_team.core.services import TaskService
from copilot_team.agents.tools.chat_tools import build_task_tools
from tests.conftest import InMemoryTaskStoreBackend


def _make_invocation(args: dict) -> ToolInvocation:
    """Create a minimal ToolInvocation for testing."""
    return ToolInvocation(
        session_id="test-session",
        tool_call_id="test-call",
        tool_name="test",
        arguments=args,
    )


async def _invoke(tool: Tool, args: dict) -> ToolResult:
    """Invoke a tool handler and return the result."""
    result = tool.handler(_make_invocation(args))
    if inspect.isawaitable(result):
        return await result
    return result


@pytest.fixture
def tools_store() -> InMemoryTaskStoreBackend:
    store = InMemoryTaskStoreBackend()
    store._stories["s1"] = Story(
        id="s1", name="Auth", description="Auth flow", status="in_progress"
    )
    store._tasks["t1"] = Task(
        id="t1", name="Login", description="Login form", story_id="s1", status="pending"
    )
    return store


@pytest.fixture
def service(tools_store: InMemoryTaskStoreBackend) -> TaskService:
    return TaskService(tools_store)


async def test_list_stories_tool(service: TaskService):
    tools = build_task_tools(service)
    list_stories = next(t for t in tools if t.name == "list_stories")
    result = await _invoke(list_stories, {})
    assert result["textResultForLlm"]


async def test_get_story_tool(service: TaskService):
    tools = build_task_tools(service)
    get_story = next(t for t in tools if t.name == "get_story")
    result = await _invoke(get_story, {"id": "s1"})
    assert result["textResultForLlm"]


async def test_create_story_tool(
    service: TaskService, tools_store: InMemoryTaskStoreBackend
):
    tools = build_task_tools(service)
    create_story = next(t for t in tools if t.name == "create_story")
    result = await _invoke(create_story, {"name": "New Story", "description": "Desc"})
    assert result["textResultForLlm"]
    assert len(tools_store._stories) == 2


async def test_update_story_tool(
    service: TaskService, tools_store: InMemoryTaskStoreBackend
):
    tools = build_task_tools(service)
    update_story = next(t for t in tools if t.name == "update_story")
    result = await _invoke(update_story, {"id": "s1", "name": "Updated Auth"})
    assert result["textResultForLlm"]
    assert tools_store._stories["s1"].name == "Updated Auth"


async def test_list_tasks_tool(service: TaskService):
    tools = build_task_tools(service)
    list_tasks = next(t for t in tools if t.name == "list_tasks")
    result = await _invoke(list_tasks, {})
    assert result["textResultForLlm"]


async def test_list_tasks_filtered_by_story(service: TaskService):
    tools = build_task_tools(service)
    list_tasks = next(t for t in tools if t.name == "list_tasks")
    result = await _invoke(list_tasks, {"story_id": "s1"})
    assert result["textResultForLlm"]
    result_empty = await _invoke(list_tasks, {"story_id": "nonexistent"})
    assert result_empty["textResultForLlm"]


async def test_get_task_tool(service: TaskService):
    tools = build_task_tools(service)
    get_task = next(t for t in tools if t.name == "get_task")
    result = await _invoke(get_task, {"id": "t1"})
    assert result["textResultForLlm"]


async def test_create_task_tool(
    service: TaskService, tools_store: InMemoryTaskStoreBackend
):
    tools = build_task_tools(service)
    create_task = next(t for t in tools if t.name == "create_task")
    result = await _invoke(
        create_task,
        {"name": "Signup", "description": "Signup form", "story_id": "s1"},
    )
    assert result["textResultForLlm"]
    assert len(tools_store._tasks) == 2


async def test_update_task_tool(
    service: TaskService, tools_store: InMemoryTaskStoreBackend
):
    tools = build_task_tools(service)
    update_task = next(t for t in tools if t.name == "update_task")
    result = await _invoke(update_task, {"id": "t1", "status": "completed"})
    assert result["textResultForLlm"]
    assert tools_store._tasks["t1"].status == "completed"
