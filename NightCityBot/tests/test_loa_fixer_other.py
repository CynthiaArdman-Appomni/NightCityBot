from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Fixer starts and ends LOA for another user."""
    logs: List[str] = []
    loa = suite.bot.get_cog('LOA')
    if not loa:
        logs.append("❌ LOA cog not loaded")
        return logs
    fixer = MagicMock()
    fixer.name = config.FIXER_ROLE_NAME
    ctx.author.roles.append(fixer)
    target = MagicMock(spec=discord.Member)
    target.roles = []
    target.add_roles = AsyncMock()
    target.remove_roles = AsyncMock()
    with patch('discord.Guild.get_role', return_value=discord.Object(id=config.LOA_ROLE_ID)):
        await loa.start_loa(ctx, target)
        target.roles.append(discord.Object(id=config.LOA_ROLE_ID))
        await loa.end_loa(ctx, target)
    suite.assert_send(logs, target.add_roles, "add_roles")
    suite.assert_send(logs, target.remove_roles, "remove_roles")
    ctx.author.roles.remove(fixer)
    return logs
