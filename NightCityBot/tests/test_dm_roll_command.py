from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING


async def run(suite, ctx) -> List[str]:
    """Relay a roll through !dm."""
    logs: List[str] = []
    dm = suite.bot.get_cog("DMHandler")
    user = await suite.get_test_user(ctx)
    ctx.send = AsyncMock()
    ctx.message.attachments = []
    roll_cog = suite.bot.get_cog("RollSystem")
    dm_channel = MagicMock(spec=discord.DMChannel)
    dm_channel.send = AsyncMock()
    with (
        patch.object(
            dm,
            "get_or_create_dm_thread",
            new=AsyncMock(return_value=MagicMock(spec=discord.Thread)),
        ),
        patch.object(
            discord.Member, "create_dm", new=AsyncMock(return_value=dm_channel)
        ),
        patch(
            "NightCityBot.cogs.dm_handling.parse_dice", return_value=(1, 20, 0)
        ) as mock_parse,
        patch.object(
            roll_cog, "loggable_roll", wraps=roll_cog.loggable_roll
        ) as mock_roll,
    ):
        await dm.dm.callback(dm, ctx, user, message="!roll 1d20")
        suite.assert_send(logs, dm_channel.send, "dm.send")
    suite.assert_called(logs, mock_parse, "parse_dice")
    suite.assert_called(logs, mock_roll, "loggable_roll")
    return logs
