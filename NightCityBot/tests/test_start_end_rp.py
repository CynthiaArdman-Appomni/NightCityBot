from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Create and end an RP session to confirm logging works."""
    logs = []
    rp_manager = suite.bot.get_cog('RPManager')
    channel = await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
    suite.debug(logs, f"start_rp created: {getattr(channel, 'name', None)}")
    if channel:
        logs.append("✅ start_rp returned a channel")
        await rp_manager.end_rp(ctx)
        suite.debug(logs, "end_rp called")
        logs.append("✅ end_rp executed without error")
    else:
        logs.append("❌ start_rp failed to create a channel")
    return logs
