"""Chat tools that expose task/story CRUD operations to the Copilot SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from copilot import define_tool
from copilot.types import Tool, ToolInvocation

if TYPE_CHECKING:
    from copilot_team.core.services import TaskService


def build_task_tools(service: TaskService) -> list[Tool]:
    """Return a list of Copilot SDK tools backed by *service*."""

    @define_tool(
        name="list_stories",
        description="List all stories. Optionally filter by status.",
    )
    async def _list_stories(
        args: dict[str, Any], _inv: ToolInvocation
    ) -> list[dict[str, Any]]:
        stories = await service.list_stories(status=args.get("status"))
        return [s.model_dump() for s in stories]

    @define_tool(name="get_story", description="Get a story by its id.")
    async def _get_story(args: dict[str, Any], _inv: ToolInvocation) -> dict[str, Any]:
        story = await service.get_story(args["id"])
        return story.model_dump()

    @define_tool(name="create_story", description="Create a new story.")
    async def _create_story(
        args: dict[str, Any], _inv: ToolInvocation
    ) -> dict[str, Any]:
        story = await service.create_story(args)
        return story.model_dump()

    @define_tool(name="update_story", description="Update an existing story by id.")
    async def _update_story(
        args: dict[str, Any], _inv: ToolInvocation
    ) -> dict[str, Any]:
        story_id = args.pop("id")
        story = await service.update_story(story_id, args)
        return story.model_dump()

    @define_tool(
        name="list_tasks",
        description="List tasks. Optionally filter by status and/or story_id.",
    )
    async def _list_tasks(
        args: dict[str, Any], _inv: ToolInvocation
    ) -> list[dict[str, Any]]:
        tasks = await service.list_tasks(
            status=args.get("status"), story_id=args.get("story_id")
        )
        return [t.model_dump() for t in tasks]

    @define_tool(name="get_task", description="Get a task by its id.")
    async def _get_task(args: dict[str, Any], _inv: ToolInvocation) -> dict[str, Any]:
        task = await service.get_task(args["id"])
        return task.model_dump()

    @define_tool(name="create_task", description="Create a new task.")
    async def _create_task(
        args: dict[str, Any], _inv: ToolInvocation
    ) -> dict[str, Any]:
        task = await service.create_task(args)
        return task.model_dump()

    @define_tool(name="update_task", description="Update an existing task by id.")
    async def _update_task(
        args: dict[str, Any], _inv: ToolInvocation
    ) -> dict[str, Any]:
        task_id = args.pop("id")
        task = await service.update_task(task_id, args)
        return task.model_dump()

    return [
        _list_stories,
        _get_story,
        _create_story,
        _update_story,
        _list_tasks,
        _get_task,
        _create_task,
        _update_task,
    ]
