from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Execute a roll as another user via !post."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    thread = MagicMock(spec=discord.Thread)
    thread.name = "rp-thread"
    parent = MagicMock()
    parent.threads = [thread]
    with patch.object(type(ctx.guild), "text_channels", new=PropertyMock(return_value=[parent])):
        ctx.message.attachments = []
        ctx.send = AsyncMock()
        with patch.object(suite.bot, "invoke", new=AsyncMock()) as mock_invoke:
            await admin.post(ctx, thread.name, message=f"!roll d20 {ctx.author.id}")
    suite.assert_called(logs, mock_invoke, "bot.invoke")
    return logs
