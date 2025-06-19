from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Create and end an RP session to confirm logging works."""
    logs = []
    rp_manager = suite.bot.get_cog('RPManager')
    channel = MagicMock(spec=discord.TextChannel)
    ctx.guild.create_text_channel = AsyncMock(return_value=channel)
    await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
    if ctx.guild.create_text_channel.await_count:
        logs.append("✅ start_rp created channel")
        ctx.channel = channel
        rp_manager.end_rp_session = AsyncMock()
        await rp_manager.end_rp(ctx)
        suite.assert_called(logs, rp_manager.end_rp_session, "end_rp_session")
    else:
        logs.append("❌ start_rp failed to create channel")
    return logs
