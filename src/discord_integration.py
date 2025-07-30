import os

import discord

from .workflow import run


class OrionClient(discord.Client):
    def __init__(self, repo_url: str | None = None, workdir: str | None = None, **kwargs) -> None:
        intents = kwargs.get("intents", discord.Intents.default())
        super().__init__(intents=intents)
        self.repo_url = repo_url or os.environ.get(
            "REPO_URL", "https://github.com/ishandutta0098/open-clip"
        )
        self.workdir = workdir or os.environ.get("WORKDIR", os.getcwd())

    async def on_ready(self) -> None:
        print(f"🤖 Logged in as {self.user}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return
        text = message.content.strip()
        if not text:
            return
        await message.channel.send(f"🤖 Running AI agent with prompt: {text}")
        run(self.repo_url, text, self.workdir)
        await message.channel.send("✅ Task completed")


def start_discord_bot(repo_url: str | None = None, workdir: str | None = None) -> None:
    """Start a Discord bot to receive prompts and run the workflow."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ Missing Discord token. Set DISCORD_BOT_TOKEN.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    client = OrionClient(repo_url=repo_url, workdir=workdir, intents=intents)
    print("🤖 Discord bot running...")
    client.run(token)
