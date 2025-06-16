from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Test passive income calculations."""
    logs = []
    user = await suite.get_test_user(ctx)
    economy = suite.bot.get_cog('Economy')

    for role in ROLE_COSTS_BUSINESS.keys():
        for count in range(5):
            income = economy.calculate_passive_income(role, count)
            logs.append(f"✅ {role} with {count} opens → ${income}")

    return logs
