"""Utility functions for the command line interface."""

from textwrap import dedent


def show_help_summary() -> None:
    """Print a summary of the available CLI commands with LangGraph features."""
    help_text = dedent(
        """
        🚀 Orion AI Agent - Intelligent Workflow System
        ===============================================
        ✨ Powered by LangGraph for intelligent orchestration

        📚 REPOSITORY MANAGEMENT:
        --list-repos       List repositories from your GitHub account
        --repo-url URL     GitHub repository URL to operate on
        --branch BRANCH    Name of the branch to operate on
        --setup-auth       Run authentication setup

        🤖 AI WORKFLOW:
        --prompt TEXT      Instruction for the AI agent
        --workdir PATH     Working directory for cloning the repository

        🔧 WORKFLOW OPTIONS:
        --debug            Enable detailed LangGraph workflow information
        --no-testing       Disable code testing of generated files
        --no-venv          Disable virtual environment creation
        --strict-testing   Abort commit if tests fail (enables smart recovery)
        --commit           Commit the generated changes
        --create-pr        Create a pull request (requires --commit)

        🤖 INTEGRATIONS:
        --discord-bot      Run the Discord bot to receive prompts
        --repo-limit N     Number of repositories to list when using --list-repos
        --show-commands    Show this help summary

        🎯 LANGGRAPH FEATURES:
        • Intelligent workflow routing based on context analysis
        • Parallel agent execution for independent tasks
        • Advanced error recovery with multiple retry strategies  
        • State-based decision making throughout workflow
        • Built-in checkpointing and state persistence

        💡 EXAMPLES:
        python main.py --prompt "Add logging functionality"
        python main.py --prompt "Build API with tests" --commit --create-pr --debug
        python main.py --prompt "Explain" --repo-url <url> --branch <branch>
        python main.py --discord-bot --debug
        """
    )
    print(help_text.strip())
