import asyncio
from unittest.mock import AsyncMock, MagicMock
import discord
from NightCityBot.cogs.character_manager import CharacterManager
from NightCityBot.cogs.test_suite import TestSuite
from NightCityBot.tests.test_copy_thread_truncate import run as run_truncate

class DummyBot:
    def __init__(self):
        self.cogs = {}
        self.loop = asyncio.new_event_loop()
    def add_cog(self, cog):
        self.cogs[cog.__class__.__name__] = cog
    def get_cog(self, name):
        return self.cogs.get(name)

class DummyCtx:
    def __init__(self):
        self.guild = MagicMock()
        self.author = MagicMock()
        self.channel = MagicMock()
        self.send = AsyncMock()
        self.message = MagicMock(attachments=[])


def setup_suite():
    bot = DummyBot()
    bot.add_cog(CharacterManager(bot))
    ts = TestSuite(bot)
    bot.add_cog(ts)
    return ts


def run_test(func):
    suite = setup_suite()
    ctx = DummyCtx()
    return asyncio.run(func(suite, ctx))


def test_copy_thread_truncate():
    logs = run_test(run_truncate)
    assert all("❌" not in l for l in logs), f"Logs: {logs}"
