from copilot_team.tui.app import CopilotTeamApp
from copilot_team.tui.screens.chat import ChatPanel
from copilot_team.tui.screens.story_form import StoryFormPanel
from copilot_team.tui.screens.task_form import TaskFormPanel
from copilot_team.tui.screens.tree_view import TreeViewPanel, StoryHeader, TaskRow
from copilot_team.tui.pydantic_form import SubModelList
from tests.conftest import InMemoryTaskStoreBackend

from textual.widgets import Input, TextArea


async def test_tree_view_shows_stories_and_tasks(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()

        headers = list(app.query(StoryHeader))
        assert len(headers) == 2
        header_labels = [str(h.story.name) for h in headers]
        assert "Dashboard" in header_labels
        assert "Auth Story" in header_labels


async def test_tree_view_shows_task_rows(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()

        rows = list(app.query(TaskRow))
        assert len(rows) == 2
        task_names = [r.task_data.name for r in rows]
        assert "Login form" in task_names
        assert "Signup form" in task_names


async def test_tree_view_shows_checklist_counts(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()

        rows = list(app.query(TaskRow))
        checklist_data = {r.task_data.name: r.task_data.checklist for r in rows}
        login_cl = checklist_data["Login form"]
        assert len(login_cl) == 2
        assert sum(1 for c in login_cl if c.completed) == 2

        signup_cl = checklist_data["Signup form"]
        assert len(signup_cl) == 2
        assert sum(1 for c in signup_cl if c.completed) == 1


async def test_tree_view_shows_status_icons(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()

        headers = list(app.query(StoryHeader))
        statuses = [h.story.status for h in headers]
        assert "in_progress" in statuses
        assert "pending" in statuses


async def test_tree_view_has_action_buttons(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        assert app.query_one("#btn-new-story")
        assert app.query_one("#btn-new-task")


async def test_tree_view_new_story_button(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        btn = app.query_one("#btn-new-story")
        btn.press()
        await pilot.pause()
        assert app.query_one(StoryFormPanel)


async def test_tree_view_new_task_button(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        btn = app.query_one("#btn-new-task")
        btn.press()
        await pilot.pause()
        assert app.query_one(TaskFormPanel)


async def test_navigate_to_chat(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.press("c")
        await pilot.pause()
        assert app.query_one(ChatPanel)


async def test_navigate_new_task_shortcut(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.press("n")
        await pilot.pause()
        assert app.query_one(TaskFormPanel)


async def test_chat_send_message(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.press("c")
        await pilot.pause()

        chat_input = app.query_one("#chat-input", Input)
        chat_input.focus()
        await pilot.pause()
        chat_input.value = "Hello AI"
        await pilot.press("enter")
        await pilot.pause()

        assert chat_input.value == ""


async def test_story_form_save(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        btn = app.query_one("#btn-new-story")
        btn.press()
        await pilot.pause()

        name_input = app.query_one("#form-name", Input)
        name_input.value = "New Story"

        desc = app.query_one("#form-description", TextArea)
        desc.load_text("A new test story")

        save_btn = app.query_one("#btn-save")
        save_btn.press()
        await pilot.pause()

        assert app.query_one(TreeViewPanel)

        stories = task_store.list_stories()
        names = [s.name for s in stories]
        assert "New Story" in names


async def test_story_form_cancel(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        app.show_story_form()
        await pilot.pause()
        assert app.query_one(StoryFormPanel)

        cancel_btn = app.query_one("#btn-cancel")
        cancel_btn.press()
        await pilot.pause()
        assert app.query_one(TreeViewPanel)


async def test_story_form_validation_empty_name(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        app.show_story_form()
        await pilot.pause()

        save_btn = app.query_one("#btn-save")
        save_btn.press()
        await pilot.pause()

        assert app.query_one(StoryFormPanel)


async def test_task_form_has_agent_and_repo_fields(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        app.show_task_form()
        await pilot.pause()

        assert app.query_one("#form-agent", Input)
        assert app.query_one("#form-repository_name", Input)


async def test_task_form_has_checklist_editor(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        app.show_task_form()
        await pilot.pause()

        assert app.query_one(SubModelList)
        assert app.query_one("#submodel-checklist-new-description", Input)
        assert app.query_one("#submodel-checklist-btn-add")


async def test_unassigned_tasks_section(task_store: InMemoryTaskStoreBackend):
    """Tasks without a story_id should appear under 'Unassigned Tasks'."""
    from copilot_team.core.models import Task

    task_store.put_task(
        Task(id="orphan", name="Orphan Task", description="No story", status="pending")
    )
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()

        unassigned = app.query_one("#unassigned-header")
        assert unassigned is not None

        rows = list(app.query(TaskRow))
        orphan_rows = [r for r in rows if r.task_data.id == "orphan"]
        assert len(orphan_rows) == 1


async def test_sidebar_always_visible(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(160, 45)) as pilot:
        await pilot.pause()
        assert app.query_one("#sidebar")
        assert app.query_one("#sidebar-menu")
        assert app.query_one("#sidebar-activity")

        await pilot.press("c")
        await pilot.pause()
        assert app.query_one("#sidebar")

        await pilot.press("t")
        await pilot.pause()
        assert app.query_one("#sidebar")
