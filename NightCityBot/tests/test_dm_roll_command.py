from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Relay a roll through !dm."""
    logs: List[str] = []
    dm = suite.bot.get_cog('DMHandler')
    user = await suite.get_test_user(ctx)
    ctx.send = AsyncMock()
    with patch.object(suite.bot.get_cog('RollSystem'), "roll", new=AsyncMock()) as mock_roll:
        await dm.dm.callback(dm, ctx, user, message="!roll 1d20")
    suite.assert_called(logs, mock_roll, "roll")
    return logs
