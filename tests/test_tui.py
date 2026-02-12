from copilot_team.tui.app import CopilotTeamApp
from copilot_team.tui.screens.chat import ChatScreen
from copilot_team.tui.screens.story_form import StoryFormScreen
from copilot_team.tui.screens.task_form import TaskFormScreen
from copilot_team.tui.screens.tree_view import TreeViewScreen
from tests.conftest import InMemoryTaskStoreBackend

from textual.widgets import Tree, Input, TextArea


async def test_tree_view_shows_stories_and_tasks(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, TreeViewScreen)

        tree = app.screen.query_one("#stories-tree", Tree)
        root = tree.root

        # Should have 2 story nodes
        assert len(root.children) == 2

        story_labels = [str(node.label) for node in root.children]
        assert any("Dashboard" in label for label in story_labels)
        assert any("Auth Story" in label for label in story_labels)


async def test_tree_view_shows_checklist_counts(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tree = app.screen.query_one("#stories-tree", Tree)

        auth_node = None
        for node in tree.root.children:
            if "Auth Story" in str(node.label):
                auth_node = node
                break

        assert auth_node is not None
        task_labels = [str(child.label) for child in auth_node.children]

        assert any("[2/2]" in label for label in task_labels)
        assert any("[1/2]" in label for label in task_labels)


async def test_tree_view_shows_status_icons(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tree = app.screen.query_one("#stories-tree", Tree)

        story_labels = [str(node.label) for node in tree.root.children]
        assert any("🔵" in label for label in story_labels)
        assert any("⬜" in label for label in story_labels)


async def test_navigate_to_story_form(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, StoryFormScreen)


async def test_navigate_to_task_form(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("a")
        await pilot.pause()
        assert isinstance(app.screen, TaskFormScreen)


async def test_navigate_to_chat(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("c")
        await pilot.pause()
        assert isinstance(app.screen, ChatScreen)


async def test_chat_send_message(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("c")
        await pilot.pause()

        chat_input = app.screen.query_one("#chat-input", Input)
        chat_input.focus()
        await pilot.pause()
        chat_input.value = "Hello AI"
        await pilot.press("enter")
        await pilot.pause()

        assert chat_input.value == ""


async def test_story_form_save(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("s")
        await pilot.pause()

        name_input = app.screen.query_one("#story-name", Input)
        name_input.value = "New Story"

        desc = app.screen.query_one("#story-description", TextArea)
        desc.load_text("A new test story")

        save_btn = app.screen.query_one("#btn-save")
        save_btn.press()
        await pilot.pause()

        assert isinstance(app.screen, TreeViewScreen)

        stories = task_store.list_stories()
        names = [s.name for s in stories]
        assert "New Story" in names


async def test_story_form_cancel(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, StoryFormScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, TreeViewScreen)


async def test_story_form_validation_empty_name(task_store: InMemoryTaskStoreBackend):
    app = CopilotTeamApp(task_store=task_store)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("s")
        await pilot.pause()

        save_btn = app.screen.query_one("#btn-save")
        save_btn.press()
        await pilot.pause()

        assert isinstance(app.screen, StoryFormScreen)
