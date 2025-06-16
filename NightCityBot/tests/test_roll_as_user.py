from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Roll on behalf of another user."""
    logs: List[str] = []
    roll = suite.bot.get_cog('RollSystem')
    user = await suite.get_test_user(ctx)
    ctx.guild.get_member = MagicMock(return_value=user)
    ctx.channel = MagicMock()
    ctx.message = MagicMock()
    ctx.message.delete = AsyncMock()
    with patch.object(roll, "loggable_roll", new=AsyncMock()) as mock_log:
        await roll.roll.callback(roll, ctx, dice=f"2d6 <@{user.id}>")
    if mock_log.await_args.args[0] == user:
        logs.append("✅ roll executed for mentioned user")
    else:
        logs.append("❌ roll did not use mentioned user")
    with patch.object(roll, "loggable_roll", new=AsyncMock()) as mock_log2:
        await roll.roll.callback(roll, ctx, dice=f"2d6 {user.id}")
    if mock_log2.await_args.args[0] == user:
        logs.append("✅ roll executed for ID user")
    else:
        logs.append("❌ roll did not use ID user")
    return logs
