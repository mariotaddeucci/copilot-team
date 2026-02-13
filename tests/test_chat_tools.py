"""Tests for chat_tools — the Copilot SDK tool definitions backed by TaskService."""

import pytest

from copilot_team.core.models import Story, Task
from copilot_team.core.services import TaskService
from copilot_team.tui.chat_tools import build_task_tools
from tests.conftest import InMemoryTaskStoreBackend


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
    result = await list_stories.handler({}, None)
    assert len(result) == 1
    assert result[0]["name"] == "Auth"


async def test_get_story_tool(service: TaskService):
    tools = build_task_tools(service)
    get_story = next(t for t in tools if t.name == "get_story")
    result = await get_story.handler({"id": "s1"}, None)
    assert result["name"] == "Auth"


async def test_create_story_tool(service: TaskService, tools_store: InMemoryTaskStoreBackend):
    tools = build_task_tools(service)
    create_story = next(t for t in tools if t.name == "create_story")
    result = await create_story.handler(
        {"name": "New Story", "description": "Desc"}, None
    )
    assert result["name"] == "New Story"
    assert len(tools_store._stories) == 2


async def test_update_story_tool(service: TaskService, tools_store: InMemoryTaskStoreBackend):
    tools = build_task_tools(service)
    update_story = next(t for t in tools if t.name == "update_story")
    result = await update_story.handler({"id": "s1", "name": "Updated Auth"}, None)
    assert result["name"] == "Updated Auth"
    assert tools_store._stories["s1"].name == "Updated Auth"


async def test_list_tasks_tool(service: TaskService):
    tools = build_task_tools(service)
    list_tasks = next(t for t in tools if t.name == "list_tasks")
    result = await list_tasks.handler({}, None)
    assert len(result) == 1
    assert result[0]["name"] == "Login"


async def test_list_tasks_filtered_by_story(service: TaskService):
    tools = build_task_tools(service)
    list_tasks = next(t for t in tools if t.name == "list_tasks")
    result = await list_tasks.handler({"story_id": "s1"}, None)
    assert len(result) == 1
    result_empty = await list_tasks.handler({"story_id": "nonexistent"}, None)
    assert len(result_empty) == 0


async def test_get_task_tool(service: TaskService):
    tools = build_task_tools(service)
    get_task = next(t for t in tools if t.name == "get_task")
    result = await get_task.handler({"id": "t1"}, None)
    assert result["name"] == "Login"


async def test_create_task_tool(service: TaskService, tools_store: InMemoryTaskStoreBackend):
    tools = build_task_tools(service)
    create_task = next(t for t in tools if t.name == "create_task")
    result = await create_task.handler(
        {"name": "Signup", "description": "Signup form", "story_id": "s1"}, None
    )
    assert result["name"] == "Signup"
    assert len(tools_store._tasks) == 2


async def test_update_task_tool(service: TaskService, tools_store: InMemoryTaskStoreBackend):
    tools = build_task_tools(service)
    update_task = next(t for t in tools if t.name == "update_task")
    result = await update_task.handler(
        {"id": "t1", "status": "completed"}, None
    )
    assert result["status"] == "completed"
    assert tools_store._tasks["t1"].status == "completed"
