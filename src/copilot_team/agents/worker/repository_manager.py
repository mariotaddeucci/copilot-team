import hashlib
from pathlib import Path

import git
from injector import Inject

from copilot_team.core.settings import Settings


class RepositoryManager:
    def __init__(self, settings: Inject[Settings]):
        self._repos_dir = settings.core.workdir / "repositories"
        self._worktrees_dir = settings.core.workdir / "worktrees"
        self._repos_dir.mkdir(parents=True, exist_ok=True)
        self._worktrees_dir.mkdir(parents=True, exist_ok=True)

    def _get_repo_path(self, url: str) -> Path:
        repository_hash = hashlib.sha1(
            url.strip().encode(), usedforsecurity=False
        ).hexdigest()[:8]
        return self._repos_dir / repository_hash

    def fetch_worktree(self, url: str) -> Path:
        repo_path = self._get_repo_path(url)
        if not repo_path.exists():
            git.Repo.clone_from(url, repo_path, bare=True)
        repo = git.Repo(repo_path)
        self._ensure_origin_fetch_refspec(repo)
        repo.remotes.origin.fetch(prune=True)
        return repo_path

    def _ensure_origin_fetch_refspec(self, repo: git.Repo) -> None:
        try:
            repo.git.config("--get-all", "remote.origin.fetch")
        except git.GitCommandError:
            repo.git.config(
                "--add",
                "remote.origin.fetch",
                "+refs/heads/*:refs/remotes/origin/*",
            )

    def _get_origin_default_branch(self, repo: git.Repo) -> str | None:
        try:
            head_ref = repo.git.symbolic_ref("refs/remotes/origin/HEAD")
            return head_ref.strip().split("/")[-1]
        except git.GitCommandError:
            if any(ref.name == "origin/main" for ref in repo.remotes.origin.refs):
                return "main"
            if any(ref.name == "origin/master" for ref in repo.remotes.origin.refs):
                return "master"
        return None

    def _ensure_local_branch(self, repo: git.Repo, branch: str) -> None:
        if branch in repo.heads:
            return

        repo.remotes.origin.fetch(prune=True)
        origin_branch = next(
            (ref for ref in repo.remotes.origin.refs if ref.name == f"origin/{branch}"),
            None,
        )

        if origin_branch is None:
            default_branch = self._get_origin_default_branch(repo)
            if default_branch is not None:
                origin_branch = next(
                    ref
                    for ref in repo.remotes.origin.refs
                    if ref.name == f"origin/{default_branch}"
                )
            elif repo.remotes.origin.refs:
                origin_branch = repo.remotes.origin.refs[0]
            else:
                raise ValueError("Unable to determine origin default branch")

        local_branch = repo.create_head(branch, origin_branch)
        local_branch.set_tracking_branch(origin_branch)

    def get_worktree_path(self, url: str, branch: str) -> Path:
        repo_path = self.fetch_worktree(url)
        repo = git.Repo(repo_path)
        self._ensure_local_branch(repo, branch)

        worktree_path = self._worktrees_dir / repo_path.name / branch
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        if not worktree_path.exists():
            repo.git.worktree("add", worktree_path, branch)
            return worktree_path

        return worktree_path
