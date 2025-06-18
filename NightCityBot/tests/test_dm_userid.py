from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Ensure !dm works with a raw user ID."""
    logs: List[str] = []
    dm = suite.bot.get_cog('DMHandler')
    user = await suite.get_test_user(ctx)
    dummy = MagicMock(spec=discord.User)
    dummy.id = user.id
    dummy.display_name = user.display_name
    ctx.send = AsyncMock()
    ctx.message.attachments = []
    with patch.object(type(dummy), "send", wraps=dummy.send) as send_mock:
        with patch.object(dm, "get_or_create_dm_thread", new=AsyncMock(return_value=MagicMock(spec=discord.Thread))):
            await dm.dm.callback(dm, ctx, dummy, message="Test")
        suite.assert_send(logs, send_mock, "user.send")
    return logs
