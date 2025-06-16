from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Run the help commands."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    ctx.send = AsyncMock()
    await admin.helpme(ctx)
    await admin.helpfixer(ctx)
    if ctx.send.await_count >= 2:
        logs.append("✅ helpme and helpfixer executed")
    else:
        logs.append("❌ Help commands failed")
    return logs
