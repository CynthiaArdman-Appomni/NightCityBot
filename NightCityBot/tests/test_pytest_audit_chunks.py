import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from NightCityBot.cogs.admin import Admin

class DummyBot:
    def __init__(self):
        self.cogs = {}
        self.loop = asyncio.new_event_loop()
    def add_cog(self, cog):
        self.cogs[cog.__class__.__name__] = cog
    def get_cog(self, name):
        return self.cogs.get(name)
    def get_channel(self, cid):
        return self.channel

class DummyCtx:
    def __init__(self):
        self.guild = MagicMock()
        self.author = MagicMock(id=42)
        self.channel = MagicMock()
        self.send = AsyncMock()
        self.message = MagicMock(attachments=[])

bot = DummyBot()
admin = Admin(bot)
bot.add_cog(admin)

async def run_test():
    ctx = DummyCtx()
    bot.channel = MagicMock(spec=discord.TextChannel)
    bot.channel.send = AsyncMock()
    await admin.log_audit(ctx.author, 'A' * 3000)
    bot.channel.send.assert_awaited()
    embed = bot.channel.send.await_args.kwargs.get('embed')
    assert embed is not None
    assert len(embed.fields) >= 3
    assert all(len(f.value) <= 1024 for f in embed.fields)


def test_audit_chunking():
    asyncio.run(run_test())
