from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Start RP with two users and roll inside."""
    logs: List[str] = []
    rp = suite.bot.get_cog('RPManager')
    user = await suite.get_test_user(ctx)
    channel = MagicMock(spec=discord.TextChannel)
    channel.name = "text-rp-test"
    rp.create_group_rp_channel = AsyncMock(return_value=channel)
    result = await rp.start_rp(ctx, f"<@{user.id}>", str(ctx.author.id))
    if result:
        logs.append("✅ start_rp handled users")
    await suite.bot.get_cog('RollSystem').loggable_roll(ctx.author, channel, "1d6")
    rp.end_rp_session = AsyncMock()
    ctx.channel = channel
    await rp.end_rp(ctx)
    suite.assert_called(logs, rp.end_rp_session, "end_rp_session")
    return logs
