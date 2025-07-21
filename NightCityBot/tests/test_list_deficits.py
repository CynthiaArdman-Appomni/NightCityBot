from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Check that list_deficits reports users with short funds."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    cyber = suite.bot.get_cog('CyberwareManager')
    if not economy or not cyber:
        logs.append('❌ required cogs not loaded')
        return logs

    user = await suite.get_test_user(ctx)
    role_h = MagicMock(spec=discord.Role)
    role_h.name = 'Housing Tier 1'
    role_b = MagicMock(spec=discord.Role)
    role_b.name = 'Business Tier 1'
    medium = discord.Object(id=config.CYBER_MEDIUM_ROLE_ID)
    checkup = discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)
    user.roles = [role_h, role_b, medium, checkup]
    from datetime import date, timedelta
    cyber.data[str(user.id)] = (date.today() - timedelta(days=7)).isoformat()
    ctx.guild.members = [user]
    ctx.send = AsyncMock()

    with patch.object(economy.unbelievaboat, 'get_balance', new=AsyncMock(return_value={'cash': 500, 'bank': 0})):
        await economy.list_deficits(ctx)
        suite.assert_send(logs, ctx.send, 'ctx.send')
        msg = ctx.send.await_args[0][0]
        if (
            'Housing Tier 1' in msg
            and 'Business Tier 1' in msg
            and 'Cyberware meds week 1' in msg
        ):
            logs.append('✅ unpaid items listed')
        else:
            logs.append(f'❌ unexpected message: {msg}')
    return logs
