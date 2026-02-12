import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field
from ulid import ULID


class TaskChecklistItem(BaseModel):
    description: str
    completed: bool = False


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(ULID()))
    category: Literal["story", "task"] = "task"
    depends_on: list["Task"] = Field(default_factory=list)
    name: str | None = None
    status: Literal["created", "planning", "enqueued", "in_progress", "completed"] = (
        "created"
    )
    description: str
    checklist: list[TaskChecklistItem] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class TaskNotFoundError(Exception): ...


class BaseTaskStoreBackend(ABC):
    @abstractmethod
    def put_task(self, task: Task) -> None: ...

    @abstractmethod
    def get_task(self, id: str) -> Task: ...

    @abstractmethod
    def list_tasks(self, status: str | None = None) -> list[Task]: ...

    def get_next_task(self, status: str) -> Task | None:
        next_task = next(
            (
                task
                for task in self.list_tasks(status=status)
                if all([dep.status == "completed" for dep in task.depends_on])
            ),
            None,
        )
        return next_task


class SqliteTaskStoreBackend(BaseTaskStoreBackend):
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS task (
                id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT NOT NULL DEFAULT 'task',
                status TEXT NOT NULL DEFAULT 'created',
                description TEXT NOT NULL,
                checklist TEXT,
                started_at TEXT,
                finished_at TEXT
            );

            CREATE TABLE IF NOT EXISTS task_dependency (
                task_id TEXT NOT NULL,
                depends_on_task_id TEXT NOT NULL,
                PRIMARY KEY (task_id, depends_on_task_id),
                FOREIGN KEY (task_id) REFERENCES task(id),
                FOREIGN KEY (depends_on_task_id) REFERENCES task(id)
            );
        """)

    def _row_to_task(self, row: sqlite3.Row, resolve_deps: bool = True) -> Task:
        checklist = None
        if row["checklist"]:
            checklist = [
                TaskChecklistItem(**item) for item in json.loads(row["checklist"])
            ]

        depends_on: list[Task] = []
        if resolve_deps:
            cursor = self.conn.execute(
                "SELECT depends_on_task_id FROM task_dependency WHERE task_id = ?",
                (row["id"],),
            )
            for dep_row in cursor.fetchall():
                dep_task = self._get_task_by_id(
                    dep_row["depends_on_task_id"], resolve_deps=False
                )
                if dep_task:
                    depends_on.append(dep_task)

        return Task(
            id=row["id"],
            name=row["name"],
            status=row["status"],
            category=row["category"],
            description=row["description"],
            checklist=checklist,
            started_at=datetime.fromisoformat(row["started_at"])
            if row["started_at"]
            else None,
            finished_at=datetime.fromisoformat(row["finished_at"])
            if row["finished_at"]
            else None,
            depends_on=depends_on,
        )

    def _get_task_by_id(self, task_id: str, resolve_deps: bool = True) -> Task | None:
        cursor = self.conn.execute("SELECT * FROM task WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_task(row, resolve_deps=resolve_deps)

    def put_task(self, task: Task) -> None:
        checklist_json = None
        if task.checklist is not None:
            checklist_json = json.dumps([item.model_dump() for item in task.checklist])

        self.conn.execute(
            """
            INSERT INTO task (id, name, category, status, description, checklist, started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                status = excluded.status,
                description = excluded.description,
                checklist = excluded.checklist,
                started_at = excluded.started_at,
                finished_at = excluded.finished_at
            """,
            (
                task.id,
                task.name,
                task.status,
                task.description,
                checklist_json,
                task.started_at.isoformat() if task.started_at else None,
                task.finished_at.isoformat() if task.finished_at else None,
            ),
        )

        self.conn.execute("DELETE FROM task_dependency WHERE task_id = ?", (task.id,))
        for dep in task.depends_on:
            self.conn.execute(
                "INSERT INTO task_dependency (task_id, depends_on_task_id) VALUES (?, ?)",
                (task.id, dep.id),
            )

        self.conn.commit()

    def get_task(self, id: str) -> Task:
        task = self._get_task_by_id(id)
        if task is None:
            raise TaskNotFoundError(f"Task with id '{id}' not found")
        return task

    def list_tasks(self, status: str | None = None) -> list[Task]:
        if status:
            cursor = self.conn.execute("SELECT * FROM task WHERE status = ?", (status,))
        else:
            cursor = self.conn.execute("SELECT * FROM task")
        return [self._row_to_task(row) for row in cursor.fetchall()]


class InMemoryTaskStoreBackend(BaseTaskStoreBackend):
    def __init__(self) -> None:
        self._sqlite_backend = SqliteTaskStoreBackend(sqlite3.connect(":memory:"))

    def put_task(self, task: Task) -> None:
        return self._sqlite_backend.put_task(task)

    def get_task(self, id: str) -> Task:
        return self._sqlite_backend.get_task(id)

    def list_tasks(self, status: str | None = None) -> list[Task]:
        return self._sqlite_backend.list_tasks(status=status)
