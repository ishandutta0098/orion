"""
Git Operations Agent for Orion AI Agent System

This agent handles all git-related operations including cloning, branching, and repository management.
"""

import os
import shutil
import subprocess
import sys
import time
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base_agent import BaseAgent


class GitOperationsAgent(BaseAgent):
    """
    Agent responsible for all git operations.

    Capabilities:
    - Clone repositories
    - Manage branches
    - Handle git state and history
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the Git Operations Agent.

        Args:
            debug: Whether to enable debug mode
        """
        super().__init__("GitOperations", debug)
        self.update_state("repositories", {})
        self.update_state("current_repo", None)
        self.update_state("current_branch", None)

    def clone_repository(
        self, repo_url: str, clone_path: str, target_branch: Optional[str] = None
    ) -> bool:
        """
        Clone a GitHub repository to the specified path.

        Args:
            repo_url: GitHub repository URL
            clone_path: Path where to clone the repository
            target_branch: Specific branch to clone (optional)

        Returns:
            bool: True if successful, False otherwise
        """

        def _clone_operation():
            if os.path.exists(clone_path):
                self.log(f"Repository already exists at {clone_path}")
                return self._handle_existing_repository(
                    clone_path, repo_url, target_branch
                )

            if target_branch:
                self.log(
                    f"Cloning repository {repo_url} (branch: {target_branch}) to {clone_path}"
                )
                subprocess.run(
                    ["git", "clone", "-b", target_branch, repo_url, clone_path],
                    check=True,
                )
            else:
                self.log(f"Cloning repository {repo_url} to {clone_path}")
                subprocess.run(["git", "clone", repo_url, clone_path], check=True)

            # Update state
            repo_name = os.path.basename(clone_path)
            self.update_state("current_repo", clone_path)
            repositories = self.get_state("repositories", {})
            repositories[repo_name] = {
                "url": repo_url,
                "path": clone_path,
                "target_branch": target_branch,
                "cloned_at": time.time(),
            }
            self.update_state("repositories", repositories)

            return True

        return (
            self.execute_with_tracking("clone_repository", _clone_operation) is not None
        )

    def _handle_existing_repository(
        self, clone_path: str, repo_url: str, target_branch: Optional[str] = None
    ) -> bool:
        """
        Handle an existing repository by validating and updating it.

        Args:
            clone_path: Path to the existing repository
            repo_url: Expected repository URL
            target_branch: Specific branch to switch to (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            original_dir = os.getcwd()
            os.chdir(clone_path)

            # Check if it's a valid git repository
            subprocess.run(["git", "status"], check=True, capture_output=True)
            self.log("✅ Using existing repository")

            # Fetch latest changes
            self.log("🔄 Fetching latest changes...")
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)

            # Switch to target branch or main/master branch
            if target_branch:
                self.log(f"🌿 Switching to target branch: {target_branch}")
                try:
                    subprocess.run(
                        ["git", "checkout", target_branch],
                        check=True,
                        capture_output=True,
                    )
                    self.update_state("current_branch", target_branch)
                except subprocess.CalledProcessError:
                    self.log(
                        f"⚠️ Could not switch to target branch {target_branch}, trying origin/{target_branch}"
                    )
                    try:
                        subprocess.run(
                            [
                                "git",
                                "checkout",
                                "-b",
                                target_branch,
                                f"origin/{target_branch}",
                            ],
                            check=True,
                            capture_output=True,
                        )
                        self.update_state("current_branch", target_branch)
                    except subprocess.CalledProcessError:
                        self.log(
                            f"❌ Could not switch to target branch {target_branch}"
                        )
                        raise Exception(f"Target branch {target_branch} does not exist")
            else:
                # Switch to main/master branch
                self._switch_to_main_branch()

            # Update state
            self.update_state("current_repo", clone_path)

            return True

        except subprocess.CalledProcessError:
            self.log(
                "⚠️ Directory exists but is not a valid git repository. Removing and cloning fresh..."
            )
            shutil.rmtree(clone_path)
            if target_branch:
                subprocess.run(
                    ["git", "clone", "-b", target_branch, repo_url, clone_path],
                    check=True,
                )
            else:
                subprocess.run(["git", "clone", repo_url, clone_path], check=True)
            return True

        finally:
            os.chdir(original_dir)

    def _switch_to_main_branch(self) -> None:
        """Switch to the main or master branch."""
        try:
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            self.update_state("current_branch", "main")
        except subprocess.CalledProcessError:
            try:
                subprocess.run(
                    ["git", "checkout", "master"], check=True, capture_output=True
                )
                self.update_state("current_branch", "master")
            except subprocess.CalledProcessError:
                self.log(
                    "⚠️ Could not switch to main/master branch, staying on current branch",
                    "warning",
                )

    def create_unique_branch(
        self, base_name: str, repo_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a unique branch name that doesn't conflict with existing branches.

        Args:
            base_name: The base name for the branch
            repo_path: Path to the git repository (uses current repo if None)

        Returns:
            str: A unique branch name, or None if failed
        """

        def _create_branch_operation():
            target_repo = repo_path or self.get_state("current_repo")
            if not target_repo:
                raise ValueError("No repository path specified and no current repo set")

            # Get list of all branches
            result = subprocess.run(
                ["git", "branch", "-a"],
                capture_output=True,
                text=True,
                check=True,
                cwd=target_repo,
            )

            existing_branches = set()
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line and not line.startswith("*"):
                    # Remove 'remotes/origin/' prefix if present
                    branch_name = line.replace("remotes/origin/", "").strip()
                    if branch_name and branch_name != "HEAD":
                        existing_branches.add(branch_name)

            # Create the full branch name with orion prefix
            full_base_name = f"orion/{base_name}"

            # Check if full base name is available
            if full_base_name not in existing_branches:
                return full_base_name

            # Generate unique name with counter
            counter = 1
            while f"orion/{base_name}-{counter}" in existing_branches:
                counter += 1

            return f"orion/{base_name}-{counter}"

        branch_name = self.execute_with_tracking(
            "create_unique_branch", _create_branch_operation
        )

        if branch_name:
            self.log(f"Generated unique branch name: {branch_name}")
            self.update_state("planned_branch", branch_name)

        return branch_name

    def create_and_switch_branch(
        self, branch_name: str, repo_path: Optional[str] = None
    ) -> bool:
        """
        Create and switch to a new branch.

        Args:
            branch_name: Name of the branch to create
            repo_path: Path to the git repository (uses current repo if None)

        Returns:
            bool: True if successful, False otherwise
        """

        def _branch_operation():
            target_repo = repo_path or self.get_state("current_repo")
            if not target_repo:
                raise ValueError("No repository path specified and no current repo set")

            original_dir = os.getcwd()
            try:
                os.chdir(target_repo)
                self.log(f"Creating and switching to branch: {branch_name}")
                subprocess.run(["git", "checkout", "-b", branch_name], check=True)

                # Update state
                self.update_state("current_branch", branch_name)
                return True

            finally:
                os.chdir(original_dir)

        return (
            self.execute_with_tracking("create_and_switch_branch", _branch_operation)
            is not None
        )

    def commit_changes(self, message: str, repo_path: Optional[str] = None) -> bool:
        """
        Stage and commit all changes in the repository.

        Args:
            message: Commit message
            repo_path: Path to the git repository (uses current repo if None)

        Returns:
            bool: True if successful, False otherwise
        """

        def _commit_operation():
            # Don't add prefix if message already has orion prefix
            if not message.startswith(":robot: [orion]"):
                formatted_message = f":robot: [orion] {message}"
            else:
                formatted_message = message

            target_repo = repo_path or self.get_state("current_repo")
            if not target_repo:
                raise ValueError("No repository path specified and no current repo set")

            original_dir = os.getcwd()
            try:
                os.chdir(target_repo)

                # Stage all changes
                self.log("Staging all changes...")
                subprocess.run(["git", "add", "."], check=True)

                # Commit changes
                self.log(f"Committing with message: {formatted_message}")
                subprocess.run(["git", "commit", "-m", formatted_message], check=True)

                # Update state
                commit_info = {
                    "message": formatted_message,
                    "timestamp": time.time(),
                    "branch": self.get_state("current_branch"),
                }
                commits = self.get_state("commits", [])
                commits.append(commit_info)
                self.update_state("commits", commits)

                return True

            finally:
                os.chdir(original_dir)

        return (
            self.execute_with_tracking("commit_changes", _commit_operation) is not None
        )

    def push_branch(
        self, branch_name: Optional[str] = None, repo_path: Optional[str] = None
    ) -> bool:
        """
        Push the current branch to origin.

        Args:
            branch_name: Name of the branch to push (uses current branch if None)
            repo_path: Path to the git repository (uses current repo if None)

        Returns:
            bool: True if successful, False otherwise
        """

        def _push_operation():
            target_repo = repo_path or self.get_state("current_repo")
            target_branch = branch_name or self.get_state("current_branch")

            if not target_repo:
                raise ValueError("No repository path specified and no current repo set")
            if not target_branch:
                raise ValueError("No branch name specified and no current branch set")

            original_dir = os.getcwd()
            try:
                os.chdir(target_repo)
                self.log(f"Pushing branch: {target_branch}")
                subprocess.run(["git", "push", "origin", target_branch], check=True)

                # Update state
                self.update_state("last_pushed_branch", target_branch)
                return True

            finally:
                os.chdir(original_dir)

        return self.execute_with_tracking("push_branch", _push_operation) is not None

    def get_repository_status(self, repo_path: Optional[str] = None) -> Optional[dict]:
        """
        Get the current status of the repository.

        Args:
            repo_path: Path to the git repository (uses current repo if None)

        Returns:
            dict: Repository status information, or None if failed
        """

        def _status_operation():
            target_repo = repo_path or self.get_state("current_repo")
            if not target_repo:
                raise ValueError("No repository path specified and no current repo set")

            original_dir = os.getcwd()
            try:
                os.chdir(target_repo)

                # Get current branch
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                current_branch = branch_result.stdout.strip()

                # Get status
                status_result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                # Count changes
                status_lines = (
                    status_result.stdout.strip().split("\n")
                    if status_result.stdout.strip()
                    else []
                )
                modified_files = [
                    line for line in status_lines if line.startswith(" M")
                ]
                added_files = [line for line in status_lines if line.startswith("A")]
                untracked_files = [
                    line for line in status_lines if line.startswith("??")
                ]

                return {
                    "current_branch": current_branch,
                    "modified_files": len(modified_files),
                    "added_files": len(added_files),
                    "untracked_files": len(untracked_files),
                    "has_changes": len(status_lines) > 0,
                    "repo_path": target_repo,
                }

            finally:
                os.chdir(original_dir)

        return self.execute_with_tracking("get_repository_status", _status_operation)

    def execute(self, action: str, **kwargs) -> any:
        """
        Main execution method for the Git Operations Agent.

        Args:
            action: The action to perform
            **kwargs: Action-specific arguments

        Returns:
            Result of the action
        """
        action_map = {
            "clone": self.clone_repository,
            "create_branch": self.create_unique_branch,
            "switch_branch": self.create_and_switch_branch,
            "commit": self.commit_changes,
            "push": self.push_branch,
            "status": self.get_repository_status,
        }

        if action not in action_map:
            self.log(f"Unknown action: {action}", "error")
            return None

        try:
            return action_map[action](**kwargs)
        except Exception as e:
            self.log(f"Error executing action {action}: {e}", "error")
            return None
