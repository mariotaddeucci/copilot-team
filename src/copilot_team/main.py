from pathlib import Path

from copilot_team.repository_manager import RepositoryManager
from copilot_team.settings import Settings


def main():
    settings = Settings(workdir=Path("/tmp/copilot/workdir"))
    repo_manager = RepositoryManager(settings)
    path = repo_manager.get_worktree_path(
        url="https://github.com/mariotaddeucci/charsetrs.git",
        branch="fooo/bar",
    )
    print(f"Worktree path: {path}")


if __name__ == "__main__":
    main()
