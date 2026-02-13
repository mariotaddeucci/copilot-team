"""Chat tools that expose task/story CRUD operations to the Copilot SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

from copilot.tools import Tool

if TYPE_CHECKING:
    from copilot_team.core.services import TaskService


def build_task_tools(service: TaskService) -> list:
    """Return a list of Copilot SDK tools backed by *service*."""

    async def _list_stories(args, _inv):
        stories = await service.list_stories(status=args.get("status"))
        return [s.model_dump() for s in stories]

    async def _get_story(args, _inv):
        story = await service.get_story(args["id"])
        return story.model_dump()

    async def _create_story(args, _inv):
        story = await service.create_story(args)
        return story.model_dump()

    async def _update_story(args, _inv):
        story_id = args.pop("id")
        story = await service.update_story(story_id, args)
        return story.model_dump()

    async def _list_tasks(args, _inv):
        tasks = await service.list_tasks(
            status=args.get("status"), story_id=args.get("story_id")
        )
        return [t.model_dump() for t in tasks]

    async def _get_task(args, _inv):
        task = await service.get_task(args["id"])
        return task.model_dump()

    async def _create_task(args, _inv):
        task = await service.create_task(args)
        return task.model_dump()

    async def _update_task(args, _inv):
        task_id = args.pop("id")
        task = await service.update_task(task_id, args)
        return task.model_dump()

    return [
        Tool(
            name="list_stories",
            description="List all stories. Optionally filter by status.",
            handler=_list_stories,
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planning", "ready", "in_progress", "completed"],
                        "description": "Filter by story status",
                    },
                },
            },
        ),
        Tool(
            name="get_story",
            description="Get a story by its id.",
            handler=_get_story,
            parameters={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Story ID"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="create_story",
            description="Create a new story.",
            handler=_create_story,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Story name"},
                    "description": {"type": "string", "description": "Story description"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planning", "ready", "in_progress", "completed"],
                        "description": "Story status",
                    },
                },
                "required": ["name", "description"],
            },
        ),
        Tool(
            name="update_story",
            description="Update an existing story by id.",
            handler=_update_story,
            parameters={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Story ID"},
                    "name": {"type": "string", "description": "New story name"},
                    "description": {"type": "string", "description": "New description"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planning", "ready", "in_progress", "completed"],
                        "description": "New status",
                    },
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="list_tasks",
            description="List tasks. Optionally filter by status and/or story_id.",
            handler=_list_tasks,
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planning", "ready", "in_progress", "completed"],
                        "description": "Filter by task status",
                    },
                    "story_id": {
                        "type": "string",
                        "description": "Filter by parent story id",
                    },
                },
            },
        ),
        Tool(
            name="get_task",
            description="Get a task by its id.",
            handler=_get_task,
            parameters={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Task ID"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="create_task",
            description="Create a new task.",
            handler=_create_task,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Task name"},
                    "description": {"type": "string", "description": "Task description"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planning", "ready", "in_progress", "completed"],
                        "description": "Task status",
                    },
                    "story_id": {"type": "string", "description": "Parent story id"},
                    "agent": {"type": "string", "description": "Assigned agent"},
                    "repository_name": {"type": "string", "description": "Repository name"},
                    "branch_name": {"type": "string", "description": "Branch name"},
                },
                "required": ["name", "description"],
            },
        ),
        Tool(
            name="update_task",
            description="Update an existing task by id.",
            handler=_update_task,
            parameters={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Task ID"},
                    "name": {"type": "string", "description": "New task name"},
                    "description": {"type": "string", "description": "New description"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "planning", "ready", "in_progress", "completed"],
                        "description": "New status",
                    },
                    "story_id": {"type": "string", "description": "Parent story id"},
                    "agent": {"type": "string", "description": "Assigned agent"},
                    "repository_name": {"type": "string", "description": "Repository name"},
                    "branch_name": {"type": "string", "description": "Branch name"},
                },
                "required": ["id"],
            },
        ),
    ]
