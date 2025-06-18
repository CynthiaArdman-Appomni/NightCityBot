from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Create and end an RP session to confirm logging works."""
    logs = []
    rp_manager = suite.bot.get_cog('RPManager')
    thread = MagicMock(spec=discord.Thread)
    ctx.channel.create_thread = AsyncMock(return_value=thread)
    await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
    if ctx.channel.create_thread.await_count:
        logs.append("✅ start_rp created thread")
        ctx.channel = thread
        rp_manager.end_rp_session = AsyncMock()
        await rp_manager.end_rp(ctx)
        suite.assert_called(logs, rp_manager.end_rp_session, "end_rp_session")
    else:
        logs.append("❌ start_rp failed to create thread")
    return logs
