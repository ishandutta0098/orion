import os
import subprocess
import sys
from typing import Optional

from .ai_generator import generate_code_changes, make_code_changes
from .code_tester import test_generated_code
from .environment_manager import (
    create_requirements_file,
    create_virtual_environment,
    get_venv_python,
    install_dependencies,
)
from .git_operations import clone_repo, get_unique_branch_name
from .github_integration import create_pr_with_composio


def run(
    repo_url: str,
    user_prompt: str,
    workdir: Optional[str] = None,
    enable_testing: bool = True,
    create_venv: bool = True,
    strict_testing: bool = False,
    commit_changes: bool = False,
    create_pr: bool = False,
) -> None:
    """Main workflow for the agent.

    Args:
        repo_url: GitHub repository URL
        user_prompt: Task description for the AI
        workdir: Working directory for cloning
        enable_testing: Whether to test the generated code
        create_venv: Whether to create a virtual environment
        strict_testing: Whether to abort on test failures
        commit_changes: Whether to commit the changes
        create_pr: Whether to create a pull request
    """
    if workdir is None:
        workdir = "repo"

    # Extract repo name from URL for branch naming and directory naming
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    base_branch_name = f"ai-update-{repo_name}"

    # Create the full path for the repository
    repo_path = os.path.join(workdir, repo_name)

    try:
        print(f"Starting AI agent workflow for: {repo_url}")
        print(f"Task: {user_prompt}")
        print(f"Testing enabled: {enable_testing}")
        print(f"Virtual environment: {create_venv}")
        print(f"Commit changes: {commit_changes}")
        print(f"Create PR: {create_pr}")

        # Clone repository to the specific repo directory
        clone_repo(repo_url, repo_path)

        # Change to repo directory
        original_dir = os.getcwd()
        os.chdir(repo_path)

        # Check if we're in a git repository
        try:
            subprocess.run(["git", "status"], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("Error: Not a valid git repository")
            return

        # Generate unique branch name
        branch_name = get_unique_branch_name(base_branch_name, repo_path)
        print(f"Generated unique branch name: {branch_name}")

        # Create new branch
        print(f"Creating new branch: {branch_name}")
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        # Generate code changes using AI
        print("Generating code changes using AI...")
        changes = generate_code_changes(user_prompt, repo_path)

        # Make the code changes
        created_files = make_code_changes(".", changes)

        # Create virtual environment and test the code (if enabled)
        if enable_testing and create_venv:
            try:
                print("\n" + "=" * 50)
                print("🧪 Setting up testing environment...")
                print("=" * 50)

                # Create virtual environment
                venv_path = create_virtual_environment(".")
                venv_python = get_venv_python(venv_path)

                # Install dependencies
                deps_installed = install_dependencies(".", venv_python)

                if deps_installed:
                    # Test the generated code
                    tests_passed = test_generated_code(".", venv_python, created_files)

                    # Create/update requirements.txt
                    create_requirements_file(".", venv_python)

                    if not tests_passed:
                        print("\n❌ Code tests failed!")
                        print(
                            "The generated code has errors that prevent it from running correctly."
                        )
                        print("You have the following options:")
                        print("1. Continue with commit anyway (not recommended)")
                        print("2. Abort and try again with a different prompt")

                        if strict_testing:
                            print("\n❌ Strict testing enabled. Aborting commit.")
                            print("Please fix the test failures and try again.")
                            sys.exit(1)
                        else:
                            # For now, we'll continue but mark it clearly
                            print("\n⚠️ Continuing with commit despite test failures...")
                            print("⚠️ The committed code may not work correctly!")
                    else:
                        print("\n✅ All tests passed! Code is ready for commit.")
                else:
                    print("⚠️ Dependency installation failed, skipping tests...")

            except Exception as e:
                print(f"⚠️ Testing setup failed: {e}")
                print("Continuing without testing...")
        elif enable_testing and not create_venv:
            print(
                "⚠️ Testing enabled but virtual environment creation disabled. Skipping tests."
            )
        else:
            print("🚀 Testing disabled, skipping virtual environment and tests...")

        # Check if we should commit changes
        if commit_changes:
            print("\n" + "=" * 50)
            print("📝 Committing changes...")
            print("=" * 50)

            # Stage and commit changes
            print("Staging and committing changes...")
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(
                ["git", "commit", "-m", f"AI-generated changes: {user_prompt}"],
                check=True,
            )

            # Push branch and create PR (if requested)
            if create_pr:
                try:
                    print(f"Pushing branch: {branch_name}")
                    subprocess.run(["git", "push", "origin", branch_name], check=True)

                    # Create pull request using Composio
                    print("Creating pull request...")
                    create_pr_with_composio(
                        repo_url,
                        f"AI-generated update: {user_prompt}",
                        f"This PR contains AI-generated changes for: {user_prompt}\n\nChanges:\n{changes}",
                        branch_name,
                    )

                except subprocess.CalledProcessError as e:
                    print(f"Failed to push branch. Error: {e}")
                    print("You may need to:")
                    print("1. Fork the repository first")
                    print("2. Ensure you have push access")
                    print(
                        "3. Set up authentication (SSH keys or personal access token)"
                    )
            else:
                print(
                    "💡 Changes committed locally. Use --create-pr to create a pull request."
                )
                print(f"💡 To push manually: git push origin {branch_name}")
        else:
            print("\n" + "=" * 50)
            print("📝 Changes generated but not committed")
            print("=" * 50)
            print("💡 Use --commit flag to commit the changes")
            print("💡 Use --commit --create-pr to commit and create a pull request")
            print(
                f"💡 Generated files: {', '.join(created_files) if created_files else 'None'}"
            )

        print("\n✅ Workflow completed!")

    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}")
        print("Make sure you have git installed and the repository URL is correct")
    except Exception as e:
        print(f"Error in workflow: {e}")
    finally:
        # Return to original directory
        os.chdir(original_dir)
