import json
import logging
import sqlite3

import aiosqlite
from injector import Inject

from copilot_team.core.exceptions import StoryNotFoundError, TaskNotFoundError
from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task, TaskChecklistItem
from copilot_team.core.settings import Settings


class SqliteTaskStoreBackend(BaseTaskStoreBackend):
    def __init__(
        self, settings: Inject[Settings], logger: Inject[logging.Logger]
    ) -> None:
        self._db_path = str(settings.core.workdir / "task_store.db")
        settings.core.workdir.mkdir(parents=True, exist_ok=True)
        self._logger = logger
        self._conn: aiosqlite.Connection | None = None
        self._logger.info(
            "SqliteTaskStoreBackend initialized with db: %s", self._db_path
        )

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._logger.debug("Opening async database connection to %s", self._db_path)
            self._conn = await aiosqlite.connect(self._db_path)
            self._conn.row_factory = sqlite3.Row
            await self._create_tables()
            self._logger.info("Database connection established and tables created")
        return self._conn

    async def _create_tables(self) -> None:
        self._logger.debug("Creating tables if not exists")
        conn = await self._get_conn()
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS story (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created'
            );
        """)

        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS task (
                id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT NOT NULL DEFAULT 'created',
                description TEXT NOT NULL,
                checklist TEXT,
                story_id TEXT,
                FOREIGN KEY (story_id) REFERENCES story(id)
            );
        """)
        self._logger.debug("Tables created successfully")

    def _row_to_story(self, row: sqlite3.Row) -> Story:
        self._logger.debug("Converting row to Story: id=%s", row["id"])
        return Story(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
        )

    async def put_story(self, story: Story) -> None:
        self._logger.info("Saving story: id=%s, name=%s", story.id, story.name)
        try:
            conn = await self._get_conn()
            await conn.execute(
                """
                INSERT INTO story (id, name, description, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    status = excluded.status
                """,
                (story.id, story.name, story.description, story.status),
            )
            await conn.commit()
            self._logger.debug("Story saved successfully: id=%s", story.id)
        except Exception:
            self._logger.error("Failed to save story: id=%s", story.id, exc_info=True)
            raise

    async def get_story(self, id: str) -> Story:
        self._logger.debug("Fetching story: id=%s", id)
        conn = await self._get_conn()
        cursor = await conn.execute("SELECT * FROM story WHERE id = ?", (id,))
        row = await cursor.fetchone()
        if row is None:
            self._logger.warning("Story not found: id=%s", id)
            raise StoryNotFoundError(f"Story with id '{id}' not found")
        return self._row_to_story(row)

    async def list_stories(self, status: str | None = None) -> list[Story]:
        self._logger.debug("Listing stories with status filter: %s", status)
        conn = await self._get_conn()
        if status:
            cursor = await conn.execute(
                "SELECT * FROM story WHERE status = ?", (status,)
            )
        else:
            cursor = await conn.execute("SELECT * FROM story")
        rows = list(await cursor.fetchall())
        self._logger.debug("Found %d stories", len(rows))
        return [self._row_to_story(row) for row in rows]

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        self._logger.debug("Converting row to Task: id=%s", row["id"])
        checklist = []
        if row["checklist"]:
            checklist = [
                TaskChecklistItem(**item) for item in json.loads(row["checklist"])
            ]

        return Task(
            id=row["id"],
            name=row["name"],
            status=row["status"],
            description=row["description"],
            checklist=checklist,
            story_id=row["story_id"],
        )

    async def _get_task_by_id(self, task_id: str) -> Task | None:
        self._logger.debug("Fetching task by id: %s", task_id)
        conn = await self._get_conn()
        cursor = await conn.execute("SELECT * FROM task WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if row is None:
            self._logger.debug("Task not found: id=%s", task_id)
            return None
        return self._row_to_task(row)

    async def put_task(self, task: Task) -> None:
        self._logger.info("Saving task: id=%s, name=%s", task.id, task.name)
        try:
            checklist_json = None
            if task.checklist is not None:
                checklist_json = json.dumps(
                    [item.model_dump() for item in task.checklist]
                )

            conn = await self._get_conn()
            await conn.execute(
                """
                INSERT INTO task (id, name, status, description, checklist, story_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    status = excluded.status,
                    description = excluded.description,
                    checklist = excluded.checklist,
                    story_id = excluded.story_id
                """,
                (
                    task.id,
                    task.name,
                    task.status,
                    task.description,
                    checklist_json,
                    task.story_id,
                ),
            )
            await conn.commit()
            self._logger.debug("Task saved successfully: id=%s", task.id)
        except Exception:
            self._logger.error("Failed to save task: id=%s", task.id, exc_info=True)
            raise

    async def get_task(self, id: str) -> Task:
        self._logger.debug("Getting task: id=%s", id)
        task = await self._get_task_by_id(id)
        if task is None:
            self._logger.warning("Task not found: id=%s", id)
            raise TaskNotFoundError(f"Task with id '{id}' not found")
        return task

    async def list_tasks(
        self, status: str | None = None, story_id: str | None = None
    ) -> list[Task]:
        self._logger.debug(
            "Listing tasks with filters: status=%s, story_id=%s", status, story_id
        )
        query = "SELECT * FROM task"
        params: list[str] = []
        conditions: list[str] = []

        if status:
            conditions.append("status = ?")
            params.append(status)
        if story_id:
            conditions.append("story_id = ?")
            params.append(story_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        conn = await self._get_conn()
        cursor = await conn.execute(query, params)
        rows = list(await cursor.fetchall())
        self._logger.debug("Found %d tasks", len(rows))
        return [self._row_to_task(row) for row in rows]
