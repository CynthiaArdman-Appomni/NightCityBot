from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch

async def run(suite, ctx) -> List[str]:
    """Check that list_deficits reports users with short funds."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    if not economy:
        logs.append('❌ Economy cog not loaded')
        return logs

    user = await suite.get_test_user(ctx)
    role_h = MagicMock(spec=discord.Role)
    role_h.name = 'Housing Tier 1'
    role_b = MagicMock(spec=discord.Role)
    role_b.name = 'Business Tier 1'
    user.roles = [role_h, role_b]
    ctx.guild.members = [user]
    ctx.send = AsyncMock()

    with patch.object(economy.unbelievaboat, 'get_balance', new=AsyncMock(return_value={'cash': 500, 'bank': 0})):
        await economy.list_deficits(ctx)
        suite.assert_send(logs, ctx.send, 'ctx.send')
    return logs
