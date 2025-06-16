from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config

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
    loa_role = MagicMock(spec=discord.Role)
    loa_role.id = config.LOA_ROLE_ID
    # Patch the get_role method at the class level to avoid issues with
    # Discord's read-only attributes when ctx.guild is a real Guild instance.
    with patch('discord.Guild.get_role', return_value=loa_role):
        await loa.start_loa.callback(loa, ctx, target)
        target.roles.append(loa_role)
        await loa.end_loa.callback(loa, ctx, target)
    suite.assert_send(logs, target.add_roles, "add_roles")
    suite.assert_send(logs, target.remove_roles, "remove_roles")
    ctx.author.roles.remove(fixer)
    return logs
