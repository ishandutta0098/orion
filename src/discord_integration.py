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
        intents = kwargs.get("intents", discord.Intents.default())
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
        print(f"🤖 Logged in as {self.user}")
        print(f"🔧 Configuration:")
        print(f"   - Repository: {self.repo_url}")
        print(f"   - Working directory: {self.workdir}")
        print(f"   - Commit changes: {self.commit_changes}")
        print(f"   - Create PR: {self.create_pr}")
        print(f"   - Enable testing: {self.enable_testing}")
        print(f"   - Create virtual env: {self.create_venv}")
        print(f"   - Strict testing: {self.strict_testing}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return
        text = message.content.strip()
        if not text:
            return

        try:
            # Send initial response
            status_msg = f"🤖 Running AI agent with prompt: {text}"
            if self.create_pr:
                status_msg += "\n📋 Will create a pull request after completion"
            elif self.commit_changes:
                status_msg += "\n💾 Will commit changes after completion"

            await message.channel.send(status_msg)

            # Run the workflow in a separate thread to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
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

            completion_msg = "✅ Task completed"
            if self.create_pr:
                completion_msg += " and pull request created"
            elif self.commit_changes:
                completion_msg += " and changes committed"

            await message.channel.send(completion_msg)

        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
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
        print("❌ Missing Discord token. Set DISCORD_BOT_TOKEN.")
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

    print("🤖 Discord bot starting...")
    print(
        "🔧 Required permissions: 68608 (Read Messages/View Channels + Send Messages + Read Message History)"
    )

    try:
        client.run(token)
    except discord.LoginFailure:
        print("❌ Invalid Discord token. Please check your DISCORD_BOT_TOKEN.")
    except discord.ConnectionClosed:
        print("❌ Discord connection was closed. Check your internet connection.")
    except Exception as e:
        print(f"❌ Bot error: {e}")
