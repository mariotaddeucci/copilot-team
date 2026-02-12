import json
import sqlite3
from abc import ABC, abstractmethod
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl


class TaskChecklistItem(BaseModel):
    description: str
    completed: bool = False


StoryStatus = Literal["created", "planning", "ready", "in_progress", "completed"]
TaskStatus = Literal["created", "planning", "ready", "in_progress", "completed"]


class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    status: StoryStatus = "created"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    agent: str | None = None
    status: TaskStatus = "created"
    description: str
    checklist: list[TaskChecklistItem] = Field(default_factory=list)
    repository_url: HttpUrl | None = None
    branch_name: str | None = None
    story_id: str | None = None


class TaskNotFoundError(Exception): ...


class StoryNotFoundError(Exception): ...


class BaseStoreBackend(ABC):
    @abstractmethod
    def put_story(self, story: Story) -> None: ...

    @abstractmethod
    def get_story(self, id: str) -> Story: ...

    @abstractmethod
    def list_stories(self, status: str | None = None) -> list[Story]: ...

    @abstractmethod
    def put_task(self, task: Task) -> None: ...

    @abstractmethod
    def get_task(self, id: str) -> Task: ...

    @abstractmethod
    def list_tasks(
        self, status: str | None = None, story_id: str | None = None
    ) -> list[Task]: ...

    def get_next_task(self, status: str) -> Task | None:
        next_task = next(
            (task for task in self.list_tasks(status=status)),
            None,
        )
        return next_task


class SqliteStoreBackend(BaseStoreBackend):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS story (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'created'
            );
        """)

        self.conn.executescript("""
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

    def _row_to_story(self, row: sqlite3.Row) -> Story:
        return Story(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
        )

    def put_story(self, story: Story) -> None:
        self.conn.execute(
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
        self.conn.commit()

    def get_story(self, id: str) -> Story:
        cursor = self.conn.execute("SELECT * FROM story WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row is None:
            raise StoryNotFoundError(f"Story with id '{id}' not found")
        return self._row_to_story(row)

    def list_stories(self, status: str | None = None) -> list[Story]:
        if status:
            cursor = self.conn.execute(
                "SELECT * FROM story WHERE status = ?", (status,)
            )
        else:
            cursor = self.conn.execute("SELECT * FROM story")
        return [self._row_to_story(row) for row in cursor.fetchall()]

    def _row_to_task(self, row: sqlite3.Row) -> Task:
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

    def _get_task_by_id(self, task_id: str, resolve_deps: bool = True) -> Task | None:
        cursor = self.conn.execute("SELECT * FROM task WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_task(row)

    def put_task(self, task: Task) -> None:
        checklist_json = None
        if task.checklist is not None:
            checklist_json = json.dumps([item.model_dump() for item in task.checklist])

        self.conn.execute(
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
        self.conn.commit()

    def get_task(self, id: str) -> Task:
        task = self._get_task_by_id(id)
        if task is None:
            raise TaskNotFoundError(f"Task with id '{id}' not found")
        return task

    def list_tasks(
        self, status: str | None = None, story_id: str | None = None
    ) -> list[Task]:
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

        cursor = self.conn.execute(query, params)
        return [self._row_to_task(row) for row in cursor.fetchall()]
