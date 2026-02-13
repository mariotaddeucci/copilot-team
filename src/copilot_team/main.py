import asyncio

from copilot_team.core.dependencies import create_injector
from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task, TaskChecklistItem

injector = create_injector()


async def setup():
    task_store = injector.get(BaseTaskStoreBackend)

    # Stories
    s1 = Story(id="s1", name="User Authentication", description="Implement login/signup flow", status="in_progress")
    s2 = Story(id="s2", name="Dashboard", description="Build main dashboard view", status="pending")
    s3 = Story(id="s3", name="API Integration", description="REST API endpoints", status="completed")
    s4 = Story(id="s4", name="Settings Page", description="User preferences and config", status="planning")
    s5 = Story(id="s5", name="Notifications", description="Push and in-app notifications", status="ready")
    for s in [s1, s2, s3, s4, s5]:
        await task_store.put_story(s)

    # Tasks for User Authentication
    await task_store.put_task(Task(
        id="t1", name="Login form", description="Create login form", story_id="s1",
        status="completed", agent="copilot", repository_name="frontend-app",
        checklist=[
            TaskChecklistItem(description="HTML template", completed=True),
            TaskChecklistItem(description="Form validation", completed=True),
        ],
    ))
    await task_store.put_task(Task(
        id="t2", name="Signup form", description="Create signup form", story_id="s1",
        status="in_progress", agent="copilot", repository_name="frontend-app",
        checklist=[
            TaskChecklistItem(description="HTML template", completed=True),
            TaskChecklistItem(description="Backend endpoint", completed=False),
        ],
    ))
    await task_store.put_task(Task(
        id="t3", name="OAuth integration", description="Google/GitHub OAuth", story_id="s1",
        status="pending", agent="copilot", repository_name="auth-service",
    ))

    # Tasks for Dashboard
    await task_store.put_task(Task(
        id="t4", name="Dashboard layout", description="Main grid layout", story_id="s2",
        status="pending", agent="designer", repository_name="ui-kit",
    ))
    await task_store.put_task(Task(
        id="t5", name="Metrics widgets", description="KPI cards and charts", story_id="s2",
        status="pending", agent="copilot", repository_name="frontend-app",
    ))

    # Tasks for API Integration
    await task_store.put_task(Task(
        id="t6", name="Auth endpoints", description="Login/logout API", story_id="s3",
        status="completed", agent="copilot", repository_name="api-server",
        checklist=[
            TaskChecklistItem(description="POST /login", completed=True),
            TaskChecklistItem(description="POST /logout", completed=True),
            TaskChecklistItem(description="POST /refresh", completed=True),
        ],
    ))
    await task_store.put_task(Task(
        id="t7", name="User CRUD", description="User management endpoints", story_id="s3",
        status="completed", agent="copilot", repository_name="api-server",
        checklist=[
            TaskChecklistItem(description="GET /users", completed=True),
            TaskChecklistItem(description="POST /users", completed=True),
        ],
    ))

    # Tasks for Settings Page
    await task_store.put_task(Task(
        id="t8", name="Profile settings", description="Edit user profile", story_id="s4",
        status="planning", agent="copilot", repository_name="frontend-app",
    ))
    await task_store.put_task(Task(
        id="t9", name="Theme selector", description="Dark/light mode toggle", story_id="s4",
        status="pending", agent="designer", repository_name="ui-kit",
    ))

    # Tasks for Notifications
    await task_store.put_task(Task(
        id="t10", name="Push service", description="Firebase push notifications", story_id="s5",
        status="ready", agent="devops-bot", repository_name="notification-svc",
        checklist=[
            TaskChecklistItem(description="Firebase setup", completed=True),
            TaskChecklistItem(description="Token management", completed=False),
            TaskChecklistItem(description="Send API", completed=False),
        ],
    ))

    # Unassigned tasks
    await task_store.put_task(Task(
        id="t11", name="Fix CI pipeline", description="Repair broken tests",
        status="in_progress", agent="devops-bot", repository_name="infra",
    ))
    await task_store.put_task(Task(
        id="t12", name="Update README", description="Project documentation",
        status="pending",
    ))
    await task_store.put_task(Task(
        id="t13", name="Dependency audit", description="Check outdated packages",
        status="pending", agent="copilot", repository_name="frontend-app",
    ))


def main():
    from copilot_team.tui.app import CopilotTeamApp

    task_store = injector.get(BaseTaskStoreBackend)
    app = CopilotTeamApp(task_store=task_store)
    app.run()


if __name__ == "__main__":
    print("Setting up...")
    asyncio.run(setup())
    print("Done.")
    main()
