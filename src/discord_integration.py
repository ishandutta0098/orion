import asyncio
import logging
import os
import re

import discord

from .code_explainer import explain_repository
from .workflow import run_intelligent_workflow


def parse_discord_input(message_content: str) -> tuple[str, str, str] | None:
    """
    Parse Discord message input in the specified format.

    Expected format:
    URL: <github_repo_url>
    BRANCH: <branch> (optional, defaults to 'main')
    TASK: <task>

    Args:
        message_content: The Discord message content

    Returns:
        tuple[str, str, str] | None: (repo_url, branch, task) or None if parsing fails
    """
    # Clean up the message content
    content = message_content.strip()

    # Use regex to extract URL, BRANCH, and TASK
    url_pattern = r"URL:\s*(.+)"
    branch_pattern = r"BRANCH:\s*(.+)"
    task_pattern = r"TASK:\s*(.+)"

    url_match = re.search(url_pattern, content, re.IGNORECASE | re.MULTILINE)
    branch_match = re.search(branch_pattern, content, re.IGNORECASE | re.MULTILINE)
    task_match = re.search(task_pattern, content, re.IGNORECASE | re.MULTILINE)

    # URL and TASK are required
    if not (url_match and task_match):
        return None

    repo_url = url_match.group(1).strip()
    task = task_match.group(1).strip()

    # Default branch to 'main' if not provided
    if branch_match and branch_match.group(1).strip():
        branch = branch_match.group(1).strip()
    else:
        branch = "main"

    return repo_url, branch, task


def _chunk_text(text: str, max_length: int = 1900):
    """Yield successive chunks of text under the Discord message limit."""
    for i in range(0, len(text), max_length):
        yield text[i : i + max_length]


class OrionClient(discord.Client):
    def __init__(
        self,
        repo_url: str | None = None,
        workdir: str | None = None,
        commit_changes: bool = False,
        create_pr: bool = False,
        enable_testing: bool = True,
        create_venv: bool = True,
        conda_env: str = "ml",
        strict_testing: bool = False,
        **kwargs,
    ) -> None:
        # Setup intents from kwargs or use defaults with required permissions
        intents = kwargs.get("intents", discord.Intents.default())
        intents.message_content = True
        intents.messages = True

        super().__init__(intents=intents)
        # Note: repo_url will now be extracted from message, but keeping for backwards compatibility
        self.default_repo_url = repo_url or os.environ.get(
            "REPO_URL", "https://github.com/ishandutta0098/open-clip"
        )
        self.workdir = workdir or os.environ.get("WORKDIR", os.getcwd())
        self.commit_changes = commit_changes
        self.create_pr = create_pr
        self.enable_testing = enable_testing
        self.create_venv = create_venv
        self.conda_env = conda_env
        self.strict_testing = strict_testing

    async def on_ready(self) -> None:
        print("=" * 60)
        print(f"🤖 **ORION AI AGENT ONLINE** 🚀")
        print(f"👤 Logged in as: {self.user}")
        print("=" * 60)
        print(f"⚙️  **CONFIGURATION:**")
        print(f"   📦 Default Repository: {self.default_repo_url}")
        print(f"   📂 Working Dir: {self.workdir}")
        print(f"   💾 Auto-commit: {'✅' if self.commit_changes else '❌'}")
        print(f"   🚀 Auto-PR: {'✅' if self.create_pr else '❌'}")
        print(f"   🧪 Testing: {'✅' if self.enable_testing else '❌'}")
        print(f"   🐍 Virtual Env: {'✅' if self.create_venv else '❌'}")
        print(f"   🐍 Conda Env: {self.conda_env}")
        print(f"   🔒 Strict Testing: {'✅' if self.strict_testing else '❌'}")
        print("=" * 60)
        print(f"📝 **Expected Input Format:**")
        print(f"   URL: <github_repo_url>")
        print(f"   BRANCH: <branch> (optional, default: 'main')")
        print(f"   TASK: <task>")
        print("=" * 60)
        print(f"✨ **Ready to process AI tasks!** ✨")
        print("=" * 60)

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return
        text = message.content.strip()
        if not text:
            return

        try:
            # Parse the Discord input format
            parsed_input = parse_discord_input(text)

            if not parsed_input:
                # Send format error message
                error_msg = (
                    "❌ **Invalid Input Format** ❌\n\n"
                    "📝 **Expected Format:**\n"
                    "```\n"
                    "URL: <github_repo_url>\n"
                    "BRANCH: <branch> (optional, defaults to 'main')\n"
                    "TASK: <task>\n"
                    "```\n\n"
                    "📌 **Example:**\n"
                    "```\n"
                    "URL: https://github.com/username/repo\n"
                    "TASK: Add a new feature to calculate fibonacci numbers\n"
                    "```\n\n"
                    "🤖 **Orion AI Agent** - Please try again with the correct format!"
                )
                await message.channel.send(error_msg)
                return

            repo_url, branch, task = parsed_input

            if task.strip().lower() == "explain":
                await message.channel.send(
                    f"📚 Generating codebase explanation for {repo_url} (branch: {branch})"
                )
                loop = asyncio.get_event_loop()
                explanation = await loop.run_in_executor(
                    None, explain_repository, repo_url, self.workdir, branch
                )
                for chunk in _chunk_text(explanation or "No explanation generated"):
                    await message.channel.send(f"```{chunk}```")
                return

            # Send initial response
            status_msg = (
                "🤖 **Hello Sir!** 👋\n\n"
                "🚀 **AI Agent Initiated** 🚀\n"
                f"📦 **Repository:** {repo_url}\n"
                f"🌿 **Branch:** {branch}\n"
                f"📝 **Task:** {task}\n\n"
                "⚡ **Status:** Processing your request...\n"
            )
            if self.create_pr:
                status_msg += (
                    "📋 **Action:** Will create a Pull Request after completion 🎯"
                )
            elif self.commit_changes:
                status_msg += "💾 **Action:** Will commit changes after completion ✨"
            else:
                status_msg += (
                    "🔄 **Action:** Will update you once processing is complete 📊"
                )

            await message.channel.send(status_msg)

            # Send progress update
            progress_msg = (
                "⚙️ **Processing in progress...** ⚙️\n\n"
                f"🔄 Cloning repository from branch '{branch}'...\n"
                "🤖 Generating AI code...\n"
                "🧪 Running tests...\n"
                "📝 Preparing output...\n\n"
                "⏳ This may take a few moments..."
            )
            progress_message = await message.channel.send(progress_msg)

            # Run the LangGraph workflow in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                run_intelligent_workflow,
                repo_url,
                task,
                self.workdir,
                self.enable_testing,
                self.create_venv,
                self.conda_env,
                self.strict_testing,
                self.commit_changes,
                self.create_pr,
                branch,  # Add branch parameter
            )

            # Delete the progress message
            try:
                await progress_message.delete()
            except:
                pass  # Ignore if message was already deleted

            # Enhanced completion message with more details
            completion_msg = "🎉 **Task Completed Successfully!** 🎉\n\n"

            if self.create_pr:
                completion_msg += "✅ **Pull Request Created** 🚀\n"
                completion_msg += "📦 **Repository Updated** with AI-generated code\n"

                # Try multiple ways to get the PR URL
                pr_url = None
                if result:
                    pr_url = result.get("pr_url")
                    if not pr_url and result.get("pr_info"):
                        pr_url = result.get("pr_info", {}).get("pr_url")

                if pr_url:
                    completion_msg += f"\n🔗 **PR Link:** {pr_url}\n"
                    completion_msg += "👀 **Ready for Review** - Check out the changes!"
                else:
                    completion_msg += (
                        "\n⚠️ **Note:** PR was created but link unavailable"
                    )
                    # Add debug information if available
                    if result:
                        completion_msg += (
                            f"\n🔧 **Debug:** Status={result.get('status', 'unknown')}"
                        )
            elif self.commit_changes:
                completion_msg += "✅ **Changes Committed** 💾\n"
                completion_msg += "📦 **Repository Updated** with AI-generated code\n"
                completion_msg += "🎯 **Status:** Ready for next steps"
            else:
                completion_msg += "✅ **Processing Complete** 🎯\n"
                completion_msg += "📊 **Analysis Finished** - Check logs for details"

            # Add execution summary if available
            if result:
                duration = result.get("duration")
                if duration:
                    completion_msg += (
                        f"\n\n⏱️ **Execution Time:** {duration:.1f} seconds"
                    )

                created_files = result.get("created_files", [])
                if created_files:
                    completion_msg += (
                        f"\n📁 **Files Created:** {len(created_files)} file(s)"
                    )
                    if len(created_files) <= 3:
                        completion_msg += f" ({', '.join(created_files)})"

                # Add status indicators
                status = result.get("status")
                if status == "completed":
                    completion_msg += "\n\n🟢 **Status:** All operations successful"
                elif status == "failed":
                    completion_msg += "\n\n🔴 **Status:** Some operations failed"
                    error = result.get("error")
                    if error:
                        completion_msg += f"\n❌ **Error:** {error[:100]}..."

            completion_msg += "\n\n🤖 **Powered by Orion AI Agent** ⚡"

            await message.channel.send(completion_msg)

        except Exception as e:
            error_msg = (
                "🚨 **Oops! Something went wrong** 🚨\n\n"
                "❌ **Error Details:**\n"
                f"```{str(e)[:200]}{'...' if len(str(e)) > 200 else ''}```\n\n"
                "🔧 **Next Steps:**\n"
                "• Check your input format\n"
                "• Verify repository access\n"
                "• Ensure branch exists\n"
                "• Contact support if issue persists\n\n"
                "🤖 **Orion AI Agent** - We'll fix this!"
            )
            await message.channel.send(error_msg)
            print(f"Error in on_message: {e}")


def start_discord_bot(
    repo_url: str | None = None,
    workdir: str | None = None,
    commit_changes: bool = False,
    create_pr: bool = False,
    enable_testing: bool = True,
    create_venv: bool = True,
    conda_env: str = "ml",
    strict_testing: bool = False,
) -> None:
    """Start a Discord bot to receive prompts and run the workflow."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("=" * 60)
        print("❌ **MISSING DISCORD TOKEN** ❌")
        print("🔑 DISCORD_BOT_TOKEN environment variable not found")
        print("💡 Please set your Discord bot token:")
        print("   export DISCORD_BOT_TOKEN='your_token_here'")
        print("=" * 60)
        return

    # Enable proper intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True

    client = OrionClient(
        repo_url=repo_url,
        workdir=workdir,
        commit_changes=commit_changes,
        create_pr=create_pr,
        enable_testing=enable_testing,
        create_venv=create_venv,
        conda_env=conda_env,
        strict_testing=strict_testing,
        intents=intents,
    )

    print("=" * 60)
    print("🚀 **STARTING ORION DISCORD BOT** 🚀")
    print("=" * 60)
    print("🔧 Required permissions: 68608")
    print("   📖 Read Messages/View Channels")
    print("   💬 Send Messages")
    print("   📚 Read Message History")
    print("=" * 60)

    try:
        client.run(token)
    except discord.LoginFailure:
        print("=" * 60)
        print("❌ **LOGIN FAILED** ❌")
        print("🔑 Invalid Discord token")
        print("💡 Please check your DISCORD_BOT_TOKEN environment variable")
        print("=" * 60)
    except discord.ConnectionClosed:
        print("=" * 60)
        print("❌ **CONNECTION CLOSED** ❌")
        print("🌐 Discord connection was lost")
        print("💡 Please check your internet connection")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Bot error: {e}")
