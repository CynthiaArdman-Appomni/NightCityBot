from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Test shop opening functionality."""
    logs = []
    try:
        correct_channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
        logs.append("→ Expected: !open_shop should succeed when run inside the business channel.")

        control = suite.bot.get_cog('SystemControl')
        if control:
            await control.set_status('open_shop', True)

        if not correct_channel:
            logs.append("→ Result: ❌ Business open channel not found")
            return logs

        original_channel = ctx.channel
        ctx.channel = correct_channel

        economy = suite.bot.get_cog('Economy')
        await economy.open_shop(ctx)
        logs.append("→ Result: ✅ !open_shop executed in correct channel")

        ctx.channel = original_channel
    except Exception as e:
        logs.append(f"❌ Exception in test_open_shop_command: {e}")
    return logs
