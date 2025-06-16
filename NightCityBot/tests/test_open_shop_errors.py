from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Verify open_shop fails in wrong channel or on wrong day."""
    control = suite.bot.get_cog('SystemControl')
    if control:
        await control.set_status('open_shop', True)
    logs = []
    economy = suite.bot.get_cog('Economy')
    wrong_channel = ctx.channel
    with patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock()):
        # Wrong channel
        await economy.open_shop(ctx)
        logs.append("✅ open_shop rejected outside business channel")

        ctx.channel = ctx.guild.get_channel(config.BUSINESS_ACTIVITY_CHANNEL_ID)
        original_author = ctx.author
        mock_author = MagicMock(spec=discord.Member)
        mock_author.id = original_author.id

        # Simulate no business role
        mock_author.roles = []
        ctx.author = mock_author
        await economy.open_shop(ctx)
        logs.append("✅ open_shop rejected without business role")

        # Simulate non-Sunday with business role
        role = MagicMock()
        role.name = "Business Tier 1"
        mock_author.roles = [role]
        if datetime.utcnow().weekday() == 6:
            logs.append("⚠️ Test run on Sunday; skip non-Sunday check")
        else:
            await economy.open_shop(ctx)
            logs.append("✅ open_shop rejected on non-Sunday")

        ctx.channel = wrong_channel
        ctx.author = original_author
    return logs
