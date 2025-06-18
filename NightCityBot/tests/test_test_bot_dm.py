from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from NightCityBot import tests

async def run(suite, ctx) -> List[str]:
    """Ensure test_bot sends results via DM when -silent is used."""
    logs: List[str] = []
    test_cog = suite.bot.get_cog('TestSuite')
    dm_channel = MagicMock()
    dm_channel.send = AsyncMock()
    ctx.send = AsyncMock()
    ctx.message.attachments = []
    # create=True allows patching even though MagicMock lacks the attribute
    with patch.object(type(ctx.author), "create_dm", new=AsyncMock(return_value=dm_channel), create=True):
        # Limit to a simple test
        test_cog.tests = {'test_help_commands': tests.TEST_FUNCTIONS['test_help_commands']}
        await test_cog.test_bot(ctx, 'test_help_commands', '-silent')
        if any('embed' in kwargs for _, kwargs in dm_channel.send.call_args_list):
            logs.append('✅ test_bot DM summary sent')
        else:
            logs.append('❌ test_bot did not send DM summary')
    return logs
