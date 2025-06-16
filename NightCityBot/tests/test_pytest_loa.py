import asyncio
from unittest.mock import AsyncMock, MagicMock
import config

from NightCityBot.cogs.loa import LOA
from NightCityBot.cogs.test_suite import TestSuite
from NightCityBot.tests.test_loa_fixer_other import run as run_fixer_other
from NightCityBot.tests.test_loa_id_check import run as run_id_check

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
        self.guild.get_member.return_value = MagicMock(id=config.TEST_USER_ID)
        self.guild.fetch_member = AsyncMock(return_value=MagicMock(id=config.TEST_USER_ID))
        self.author = MagicMock(roles=[], display_name="Author")
        self.channel = MagicMock()
        self.send = AsyncMock()
        self.message = MagicMock(attachments=[])

def setup_suite():
    bot = DummyBot()
    bot.add_cog(LOA(bot))
    return TestSuite(bot)


def run_test(func):
    suite = setup_suite()
    ctx = DummyCtx()
    return asyncio.run(func(suite, ctx))


def test_loa_fixer_other():
    logs = run_test(run_fixer_other)
    assert all("❌" not in l for l in logs), f"Logs: {logs}"


def test_loa_id_check():
    logs = run_test(run_id_check)
    assert all("❌" not in l for l in logs), f"Logs: {logs}"
