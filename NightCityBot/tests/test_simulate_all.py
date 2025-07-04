from typing import List
from unittest.mock import AsyncMock, patch
import discord
import config


async def run(suite, ctx) -> List[str]:
    """Run simulate_all for a single user."""
    logs: List[str] = []
    economy = suite.bot.get_cog("Economy")
    cyber = suite.bot.get_cog("CyberwareManager")
    admin = suite.bot.get_cog("Admin")
    user = await suite.get_test_user(ctx)
    approved = discord.Object(id=config.APPROVED_ROLE_ID)
    user.roles = [approved]
    ctx.send = AsyncMock()
    with (
        patch.object(
            economy.unbelievaboat,
            "get_balance",
            new=AsyncMock(return_value={"cash": 1000, "bank": 0}),
        ),
        patch.object(
            economy.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)
        ),
        patch.object(
            cyber.unbelievaboat,
            "get_balance",
            new=AsyncMock(return_value={"cash": 1000, "bank": 0}),
        ),
        patch.object(
            cyber.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)
        ),
        patch.object(admin, "log_audit", new=AsyncMock()) as mock_audit,
        patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
    ):
        await economy.simulate_all(ctx, target_user=user)
        suite.assert_called(logs, mock_audit, "log_audit")
        messages = [c.args[0] for c in ctx.send.await_args_list if c.args]
        if any("Baseline living cost" in m for m in messages):
            logs.append("✅ baseline shown")
        else:
            logs.append("❌ baseline missing")
    return logs
