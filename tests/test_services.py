"""Tests for the TaskService service layer."""

import pytest

from copilot_team.core.models import Story, Task
from copilot_team.core.services import ChatService, TaskService
from tests.conftest import InMemoryTaskStoreBackend


@pytest.fixture
def store() -> InMemoryTaskStoreBackend:
    s = InMemoryTaskStoreBackend()
    s._stories["s1"] = Story(
        id="s1", name="Auth", description="Auth flow", status="in_progress"
    )
    s._tasks["t1"] = Task(
        id="t1", name="Login", description="Login form", story_id="s1", status="pending"
    )
    s._tasks["t2"] = Task(
        id="t2", name="Orphan", description="No story", status="pending"
    )
    return s


@pytest.fixture
def svc(store: InMemoryTaskStoreBackend) -> TaskService:
    return TaskService(store)


# ── Stories ───────────────────────────────────────────────


async def test_list_stories(svc: TaskService):
    stories = await svc.list_stories()
    assert len(stories) == 1
    assert stories[0].name == "Auth"


async def test_list_stories_filter(svc: TaskService):
    assert await svc.list_stories(status="pending") == []
    result = await svc.list_stories(status="in_progress")
    assert len(result) == 1


async def test_get_story(svc: TaskService):
    story = await svc.get_story("s1")
    assert story.name == "Auth"


async def test_create_story(svc: TaskService, store: InMemoryTaskStoreBackend):
    story = await svc.create_story({"name": "New", "description": "Desc"})
    assert story.name == "New"
    assert story.id in store._stories


async def test_update_story(svc: TaskService, store: InMemoryTaskStoreBackend):
    updated = await svc.update_story("s1", {"name": "Updated"})
    assert updated.name == "Updated"
    assert store._stories["s1"].name == "Updated"


async def test_save_story(svc: TaskService, store: InMemoryTaskStoreBackend):
    story = Story(id="s2", name="Dashboard", description="Desc", status="pending")
    result = await svc.save_story(story)
    assert result.id == "s2"
    assert "s2" in store._stories


# ── Tasks ────────────────────────────────────────────────


async def test_list_tasks(svc: TaskService):
    tasks = await svc.list_tasks()
    assert len(tasks) == 2


async def test_list_tasks_by_story(svc: TaskService):
    tasks = await svc.list_tasks(story_id="s1")
    assert len(tasks) == 1
    assert tasks[0].name == "Login"


async def test_list_unassigned_tasks(svc: TaskService):
    unassigned = await svc.list_unassigned_tasks()
    assert len(unassigned) == 1
    assert unassigned[0].name == "Orphan"


async def test_get_task(svc: TaskService):
    task = await svc.get_task("t1")
    assert task.name == "Login"


async def test_create_task(svc: TaskService, store: InMemoryTaskStoreBackend):
    task = await svc.create_task({"name": "Signup", "description": "Signup form"})
    assert task.name == "Signup"
    assert task.id in store._tasks


async def test_update_task(svc: TaskService, store: InMemoryTaskStoreBackend):
    updated = await svc.update_task("t1", {"status": "completed"})
    assert updated.status == "completed"
    assert store._tasks["t1"].status == "completed"


async def test_save_task(svc: TaskService, store: InMemoryTaskStoreBackend):
    task = Task(id="t3", name="New", description="Desc", status="pending")
    result = await svc.save_task(task)
    assert result.id == "t3"
    assert "t3" in store._tasks


def test_chat_service_enqueue_and_pop():
    chat = ChatService()
    assert chat.enqueue_message("hello") is False
    assert chat.enqueue_message("world") is True
    assert chat.next_message() == "hello"
    assert chat.next_message() == "world"
    assert chat.next_message() is None


def test_chat_service_enqueue_while_processing():
    chat = ChatService()
    chat.set_processing(True)
    assert chat.enqueue_message("queued") is True
