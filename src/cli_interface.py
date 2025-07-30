def show_help_summary():
    """Show a helpful summary of available commands."""
    print("\n" + "=" * 60)
    print("🚀 Orion AI Agent - Available Commands")
    print("=" * 60)
    print()
    print("📋 Repository Management:")
    print(
        "  python src/agent.py --list-repos                    # List your repositories"
    )
    print(
        "  python src/agent.py --list-repos --repo-limit 10    # List 10 repositories"
    )
    print()
    print("🔧 Authentication:")
    print(
        "  python src/agent.py --setup-auth                    # Setup GitHub authentication"
    )
    print("  python auth_setup.py                                # Direct auth setup")
    print()
    print("🤖 AI Agent Operations:")
    print("  python src/agent.py --repo-url <url> --prompt <task>")
    print("  python src/agent.py --repo-url https://github.com/owner/repo \\")
    print("                      --prompt 'Add authentication to the API'")
    print()
    print("📝 Commit & PR Options:")
    print("  python src/agent.py --repo-url <url> --prompt <task> --commit")
    print("  python src/agent.py --repo-url <url> --prompt <task> --commit --create-pr")
    print("  # --commit: Commit the generated changes")
    print("  # --create-pr: Create a pull request (requires --commit)")
    print()
    print("🧪 Testing Options:")
    print("  python src/agent.py --repo-url <url> --prompt <task> --no-testing")
    print("  python src/agent.py --repo-url <url> --prompt <task> --no-venv")
    print("  python src/agent.py --repo-url <url> --prompt <task> --strict-testing")
    print("  # --no-testing: Skip code testing")
    print("  # --no-venv: Skip virtual environment creation")
    print("  # --strict-testing: Abort commit if tests fail")
    print()
    print("🔍 Debug Mode:")
    print(
        "  python src/agent.py --list-repos --debug            # Show raw API responses"
    )
    print()
    print("📚 Setup & Help:")
    print("  python setup_guide.py                               # Initial setup guide")
    print("  python src/agent.py --help                          # Show all options")
    print()
    print("🌐 Useful Links:")
    print("  • Composio Dashboard: https://app.composio.dev/")
    print("  • OpenAI API Keys: https://platform.openai.com/api-keys")
    print("  • GitHub: https://github.com/")
    print("=" * 60)
