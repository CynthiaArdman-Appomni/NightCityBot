from typing import List
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS

async def run(suite, ctx) -> List[str]:
    """Test passive income calculations."""
    logs = []
    economy = suite.bot.get_cog('Economy')

    for role in ROLE_COSTS_BUSINESS.keys():
        for count in range(5):
            income = economy.calculate_passive_income(role, count)
            logs.append(f"✅ {role} with {count} opens → ${income}")

    return logs
