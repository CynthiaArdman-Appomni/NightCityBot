from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Send an anonymous DM."""
    logs: List[str] = []
    dm = suite.bot.get_cog('DMHandler')
    user = await suite.get_test_user(ctx)
    user.send = AsyncMock()
    ctx.send = AsyncMock()
    ctx.message.attachments = []
    with patch.object(dm, "get_or_create_dm_thread", new=AsyncMock(return_value=MagicMock(spec=discord.Thread))):
        await dm.dm.callback(dm, ctx, user, message="Hello there!")
    suite.assert_send(logs, user.send, "user.send")
    return logs
