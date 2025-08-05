import asyncio
import logging
import os

import discord

from .workflow import run


class OrionClient(discord.Client):
    def __init__(
        self,
        repo_url: str | None = None,
        workdir: str | None = None,
        commit_changes: bool = False,
        create_pr: bool = False,
        enable_testing: bool = True,
        create_venv: bool = True,
        strict_testing: bool = False,
        **kwargs,
    ) -> None:
        # Setup intents from kwargs or use defaults with required permissions
        intents = kwargs.get("intents", discord.Intents.default())
        intents.message_content = True
        intents.messages = True

        super().__init__(intents=intents)
        self.repo_url = repo_url or os.environ.get(
            "REPO_URL", "https://github.com/ishandutta0098/open-clip"
        )
        self.workdir = workdir or os.environ.get("WORKDIR", os.getcwd())
        self.commit_changes = commit_changes
        self.create_pr = create_pr
        self.enable_testing = enable_testing
        self.create_venv = create_venv
        self.strict_testing = strict_testing

    async def on_ready(self) -> None:
        print("=" * 60)
        print(f"🤖 **ORION AI AGENT ONLINE** 🚀")
        print(f"👤 Logged in as: {self.user}")
        print("=" * 60)
        print(f"⚙️  **CONFIGURATION:**")
        print(f"   📦 Repository: {self.repo_url}")
        print(f"   📂 Working Dir: {self.workdir}")
        print(f"   💾 Auto-commit: {'✅' if self.commit_changes else '❌'}")
        print(f"   🚀 Auto-PR: {'✅' if self.create_pr else '❌'}")
        print(f"   🧪 Testing: {'✅' if self.enable_testing else '❌'}")
        print(f"   🐍 Virtual Env: {'✅' if self.create_venv else '❌'}")
        print(f"   🔒 Strict Testing: {'✅' if self.strict_testing else '❌'}")
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
            # Send initial response
            status_msg = (
                "🤖 **Hello Sir!** 👋\n\n"
                "🚀 **AI Agent Initiated** 🚀\n"
                f"📝 **Task:** {text}\n\n"
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
                "🔄 Cloning repository...\n"
                "🤖 Generating AI code...\n"
                "🧪 Running tests...\n"
                "📝 Preparing output...\n\n"
                "⏳ This may take a few moments..."
            )
            progress_message = await message.channel.send(progress_msg)

            # Run the workflow in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                run,
                self.repo_url,
                text,
                self.workdir,
                self.enable_testing,
                self.create_venv,
                self.strict_testing,
                self.commit_changes,
                self.create_pr,
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
                if result and result.get("pr_url"):
                    completion_msg += f"\n🔗 **PR Link:** {result.get('pr_url')}\n"
                    completion_msg += "👀 **Ready for Review** - Check out the changes!"
                else:
                    completion_msg += (
                        "\n⚠️ **Note:** PR was created but link unavailable"
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
                "• Check your configuration\n"
                "• Verify repository access\n"
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
