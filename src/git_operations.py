import os
import subprocess
from typing import Optional


def clone_repo(repo_url: str, clone_path: str) -> None:
    """Clone a GitHub repo to `clone_path` or use existing repo if it exists."""
    if os.path.exists(clone_path):
        print(f"Repository already exists at {clone_path}")
        # Check if it's a valid git repository
        try:
            original_dir = os.getcwd()
            os.chdir(clone_path)
            subprocess.run(["git", "status"], check=True, capture_output=True)
            print("✅ Using existing repository")
            # Fetch latest changes
            print("🔄 Fetching latest changes...")
            subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
            # Switch to main/master branch
            try:
                subprocess.run(
                    ["git", "checkout", "main"], check=True, capture_output=True
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(
                        ["git", "checkout", "master"], check=True, capture_output=True
                    )
                except subprocess.CalledProcessError:
                    print(
                        "⚠️ Could not switch to main/master branch, staying on current branch"
                    )
            os.chdir(original_dir)
        except subprocess.CalledProcessError:
            print(
                f"⚠️ Directory exists but is not a valid git repository. Removing and cloning fresh..."
            )
            import shutil

            shutil.rmtree(clone_path)
            print(f"Cloning repository {repo_url} to {clone_path}")
            subprocess.run(["git", "clone", repo_url, clone_path], check=True)
        return

    print(f"Cloning repository {repo_url} to {clone_path}")
    subprocess.run(["git", "clone", repo_url, clone_path], check=True)


def get_unique_branch_name(base_name: str, repo_path: str) -> str:
    """Generate a unique branch name that doesn't conflict with existing branches.

    Args:
        base_name: The base name for the branch
        repo_path: Path to the git repository

    Returns:
        str: A unique branch name
    """
    try:
        # Get list of all branches (local and remote)
        result = subprocess.run(
            ["git", "branch", "-a"],
            capture_output=True,
            text=True,
            check=True,
            cwd=repo_path,
        )
        existing_branches = set()
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line and not line.startswith("*"):
                # Remove 'remotes/origin/' prefix if present
                branch_name = line.replace("remotes/origin/", "").strip()
                if branch_name and branch_name != "HEAD":
                    existing_branches.add(branch_name)

        # Check if base_name is available
        if base_name not in existing_branches:
            return base_name

        # Generate unique name with counter
        counter = 1
        while f"{base_name}-{counter}" in existing_branches:
            counter += 1

        return f"{base_name}-{counter}"

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Could not get branch list: {e}")
        # Fallback: use timestamp
        import time

        timestamp = int(time.time())
        return f"{base_name}-{timestamp}"
