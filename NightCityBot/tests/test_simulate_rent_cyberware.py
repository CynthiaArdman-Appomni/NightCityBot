from typing import List
import discord
from unittest.mock import AsyncMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Run simulate_rent with -cyberware flag."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    cyber = suite.bot.get_cog('CyberwareManager')
    user = await suite.get_test_user(ctx)
    # Give user a cyberware role and checkup role
    medium = discord.Object(id=config.CYBER_MEDIUM_ROLE_ID)
    checkup = discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)
    approved = discord.Object(id=config.APPROVED_ROLE_ID)
    user.roles = [medium, checkup, approved]
    cyber.data[str(user.id)] = 0
    ctx.send = AsyncMock()
    with (
        patch.object(economy.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 1000, "bank": 0})),
        patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
        patch.object(cyber.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 1000, "bank": 0})),
        patch.object(cyber.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
        patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
    ):
        await economy.simulate_rent(ctx, "-cyberware", target_user=user)
    messages = [c.args[0] for c in ctx.send.await_args_list if c.args]
    if any("Cyberware meds week" in m for m in messages):
        logs.append("✅ cyberware cost included")
    else:
        logs.append("❌ cyberware cost missing")
    return logs
