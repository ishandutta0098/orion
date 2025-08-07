#!/usr/bin/env python3
"""
Orion AI Agent - Main Entry Point

This script orchestrates AI-powered code generation for GitHub repositories using
LangGraph for intelligent workflow orchestration, parallel processing, and advanced
error recovery capabilities.
"""

import argparse
import os
import subprocess
import sys

from dotenv import load_dotenv

from src.agents import GitHubIntegrationAgent
from src.cli_interface import show_help_summary
from src.code_explainer import explain_repository
from src.discord_integration import start_discord_bot

# Import LangGraph workflow as the default
from src.workflow import run_intelligent_workflow

# Load environment variables
load_dotenv()


def main():
    """Main entry point for the Orion AI Agent with LangGraph orchestration."""
    parser = argparse.ArgumentParser(
        description="Run Orion AI agent with intelligent LangGraph workflow orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚀 LANGGRAPH FEATURES:
  • Intelligent workflow routing based on context analysis
  • Parallel agent execution for improved performance  
  • Advanced error recovery with multiple retry strategies
  • State-based decision making throughout workflow
  • Built-in checkpointing and state persistence
  • Dynamic workflow adaptation based on repository analysis

💡 TIP: Use --debug for detailed workflow information!
💡 TIP: Use --conda-env [env_name] to specify conda environment (default: ml)
💡 TIP: Use --no-venv to skip environment creation and use conda instead
        """,
    )
    parser.add_argument(
        "--list-repos",
        action="store_true",
        help="List repositories from your GitHub account",
    )
    parser.add_argument(
        "--repo-url",
        help="GitHub repository URL",
        default="https://github.com/ishandutta0098/open-clip",
    )
    parser.add_argument(
        "--branch",
        help="Name of the branch to work on",
        default=None,
    )
    parser.add_argument(
        "--prompt",
        help="Instruction for the AI agent",
        default="Create a python script to use clip model from transformers library",
    )
    parser.add_argument(
        "--workdir",
        help="Working directory for cloning",
        default="/Users/ishandutta/Documents/code/orion-backend",
    )
    parser.add_argument(
        "--repo-limit",
        type=int,
        default=5,
        help="Number of repositories to list (default: 5)",
    )
    parser.add_argument(
        "--setup-auth", action="store_true", help="Run authentication setup"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to show raw API responses",
    )
    parser.add_argument(
        "--show-commands",
        action="store_true",
        help="Show available commands and examples",
    )
    parser.add_argument(
        "--no-testing", action="store_true", help="Disable code testing"
    )
    parser.add_argument(
        "--no-venv", action="store_true", help="Disable virtual environment creation"
    )
    parser.add_argument(
        "--conda-env",
        help="Conda environment to use for running code",
        default="ml",
    )
    parser.add_argument(
        "--strict-testing", action="store_true", help="Abort commit if tests fail"
    )
    parser.add_argument(
        "--commit", action="store_true", help="Commit the generated changes"
    )
    parser.add_argument(
        "--create-pr",
        action="store_true",
        help="Create a pull request (requires --commit)",
    )
    parser.add_argument(
        "--discord-bot",
        action="store_true",
        help="Run Discord bot to receive prompts",
    )
    args = parser.parse_args()

    if args.create_pr:
        args.commit = True

    # Set debug mode if requested
    if args.debug:
        os.environ["DEBUG"] = "true"
        print(
            "🔧 Debug mode enabled - detailed LangGraph workflow information will be shown"
        )

    # Validate argument combinations
    if args.create_pr and not args.commit:
        print("❌ Error: --create-pr requires --commit")
        print(
            "💡 Use: --commit --create-pr to commit changes and create a pull request"
        )
        sys.exit(1)

    if args.discord_bot:
        start_discord_bot(
            repo_url=args.repo_url,
            workdir=args.workdir,
            commit_changes=args.commit,
            create_pr=args.create_pr,
            enable_testing=not args.no_testing,
            create_venv=not args.no_venv,
            conda_env=args.conda_env,
            strict_testing=args.strict_testing,
        )
        return

    if args.show_commands:
        show_help_summary()
    elif args.setup_auth:
        print("🔧 Running authentication setup...")
        subprocess.run(["python", "src/auth_setup.py"])
    elif args.list_repos:
        print("📚 Listing repositories from your GitHub account...")

        # Use the new GitHub Integration Agent
        github_agent = GitHubIntegrationAgent(debug=args.debug)
        result = github_agent.list_repositories(args.repo_limit)

        if result:
            print(result)
        else:
            print("❌ Failed to list repositories")

        print("\n💡 Tip: Use --debug flag for detailed LangGraph workflow information")
        print("💡 Tip: LangGraph provides intelligent routing and error recovery")
        print(
            "💡 Tip: Run 'python main.py --show-commands' to see all available commands"
        )
    else:
        # Check authentication before running the main workflow
        github_agent = GitHubIntegrationAgent(debug=args.debug)
        if not github_agent.check_authentication():
            print(
                "\n💡 Tip: Run 'python main.py --setup-auth' to set up authentication"
            )
            print(
                "💡 Tip: Run 'python main.py --show-commands' to see all available commands"
            )
            sys.exit(1)

        if args.prompt.strip().lower() == "explain":
            if args.commit or args.create_pr:
                print("ℹ️ Explanation mode ignores commit and PR options.")
            explain_repository(
                args.repo_url,
                args.workdir,
                branch=args.branch,
            )
            return

        print(f"🤖 Running AI agent on repository: {args.repo_url}")
        print(f"📝 Task: {args.prompt}")
        print("✨ Using LangGraph for intelligent workflow orchestration")
        run_intelligent_workflow(
            args.repo_url,
            args.prompt,
            args.workdir,
            enable_testing=not args.no_testing,
            create_venv=not args.no_venv,
            conda_env=args.conda_env,
            strict_testing=args.strict_testing,
            commit_changes=args.commit,
            create_pr=args.create_pr,
            branch=args.branch,
        )


if __name__ == "__main__":
    main()
