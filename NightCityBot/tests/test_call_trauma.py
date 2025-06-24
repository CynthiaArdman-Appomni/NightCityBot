from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config


async def run(suite, ctx) -> List[str]:
    """Ensure call_trauma pings the Trauma Team channel."""
    logs: List[str] = []
    cog = suite.bot.get_cog('TraumaTeam')
    if not cog:
        logs.append('❌ TraumaTeam cog not loaded')
        return logs

    trauma_channel = MagicMock(spec=discord.TextChannel)
    trauma_channel.send = AsyncMock()
    with patch.object(ctx.guild, 'get_channel', return_value=trauma_channel):
        role = MagicMock(spec=discord.Role)
        role.name = 'Trauma Team Gold'
        ctx.author.roles = [role]
        ctx.send = AsyncMock()
        await cog.call_trauma(ctx)
    suite.assert_send(logs, trauma_channel.send, 'send')
    return logs

