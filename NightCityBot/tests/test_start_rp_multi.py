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
    thread = MagicMock(spec=discord.Thread)
    ctx.channel.create_thread = AsyncMock(return_value=thread)
    await rp.start_rp(ctx, f"<@{user.id}>", str(ctx.author.id))
    if ctx.channel.create_thread.await_count:
        logs.append("✅ start_rp handled users")
        await suite.bot.get_cog('RollSystem').loggable_roll(ctx.author, thread, "1d6")
        rp.end_rp_session = AsyncMock()
        ctx.channel = thread
        await rp.end_rp(ctx)
        suite.debug(logs, "end_rp called in multi")
        suite.assert_called(logs, rp.end_rp_session, "end_rp_session")
    else:
        logs.append("❌ start_rp failed to create thread")
    return logs
