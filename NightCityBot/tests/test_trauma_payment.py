from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Test Trauma Team subscription processing."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        approved = discord.Object(id=config.APPROVED_ROLE_ID)
        user.roles = [approved]
        logs.append("→ Expected: collect_trauma should find thread and log subscription payment.")

        economy = suite.bot.get_cog('Economy')
        await economy.collect_trauma(ctx, f"<@{user.id}>")
        logs.append("→ Result: ✅ Trauma Team logic executed on live user (check #tt-plans-payment).")
    except Exception as e:
        logs.append(f"❌ Exception in test_trauma_payment: {e}")
    return logs
