"""Utility functions for the command line interface."""
from textwrap import dedent


def show_help_summary() -> None:
    """Print a summary of the available CLI commands used in ``main.py``."""
    help_text = dedent(
        """
        Orion CLI Commands
        ==================

        --list-repos       List repositories from your GitHub account
        --repo-url URL     GitHub repository URL to operate on
        --prompt TEXT      Instruction for the AI agent
        --workdir PATH     Working directory for cloning the repository
        --repo-limit N     Number of repositories to list when using --list-repos
        --setup-auth       Run authentication setup
        --debug            Enable debug mode
        --show-commands    Show this help summary
        --no-testing       Disable code testing of generated files
        --no-venv          Disable virtual environment creation
        --strict-testing   Abort commit if tests fail
        --commit           Commit the generated changes
        --create-pr        Create a pull request (requires --commit)
        --discord-bot      Run the Discord bot to receive prompts
        """
    )
    print(help_text.strip())
