from typing import List
import discord
import os
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Test all rent-related commands."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        logs.append("→ Expected: All rent-related commands should complete without error.")

        if os.path.exists(config.LAST_RENT_FILE):
            os.remove(config.LAST_RENT_FILE)

        economy = suite.bot.get_cog('Economy')
        await economy.collect_rent(ctx)
        logs.append("✅ collect_rent (global) executed")

        if os.path.exists(config.LAST_RENT_FILE):
            os.remove(config.LAST_RENT_FILE)

        await economy.collect_rent(ctx, target_user=user)
        logs.append("✅ collect_rent (specific user) executed")

        await economy.collect_housing(ctx, f"<@{user.id}>")
        logs.append("✅ collect_housing executed")

        await economy.collect_business(ctx, f"<@{user.id}>")
        logs.append("✅ collect_business executed")

        await economy.collect_trauma(ctx, f"<@{user.id}>")
        logs.append("✅ collect_trauma executed")

        logs.append("→ Result: ✅ All rent commands executed.")
    except Exception as e:
        logs.append(f"❌ Exception in test_full_rent_commands: {e}")
    return logs
