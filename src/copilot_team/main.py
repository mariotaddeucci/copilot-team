from copilot_team.core.dependencies import create_injector
from copilot_team.core.interfaces import BaseTaskStoreBackend
from copilot_team.core.models import Story, Task

injector = create_injector()


def setup():
    task_store = injector.get(BaseTaskStoreBackend)
    story = Story(id="story1", name="Test Story", description="A test story")
    task_store.put_story(story)

    task = Task(
        id="task1",
        name="Test Task",
        description="A test task",
        story_id=story.id,
    )
    task_store.put_task(task)


def main():
    print("Setting up...")


if __name__ == "__main__":
    print("Setting up...")
    setup()
    print("Done.")
    main()
