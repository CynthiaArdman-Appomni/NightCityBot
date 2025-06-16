from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Ensure LOA start and end commands execute."""
    control = suite.bot.get_cog('SystemControl')
    if control:
        await control.set_status('loa', True)
    logs = []
    loa = suite.bot.get_cog('LOA')
    if not loa:
        logs.append("❌ LOA cog not loaded")
        return logs
    original_author = ctx.author
    mock_author = MagicMock(spec=discord.Member)
    mock_author.id = original_author.id
    mock_author.roles = []
    mock_author.add_roles = AsyncMock()
    mock_author.remove_roles = AsyncMock()
    ctx.author = mock_author
    loa_role = discord.Object(id=config.LOA_ROLE_ID)
    with patch('discord.Guild.get_role', return_value=loa_role):
        await loa.start_loa(ctx)
        mock_author.roles.append(loa_role)
        await loa.end_loa(ctx)
    suite.assert_send(logs, mock_author.add_roles, "add_roles")
    suite.assert_send(logs, mock_author.remove_roles, "remove_roles")
    ctx.author = original_author
    return logs
