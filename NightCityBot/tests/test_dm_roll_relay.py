from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING


async def run(suite, ctx) -> List[str]:
    """Test relaying roll commands through DMs."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        dm_handler = suite.bot.get_cog("DMHandler")
        dummy_thread = MagicMock(spec=discord.Thread)
        dm_channel = MagicMock(spec=discord.DMChannel)
        dm_channel.send = AsyncMock()
        roll_cog = suite.bot.get_cog("RollSystem")
        with (
            patch.object(
                dm_handler,
                "get_or_create_dm_thread",
                new=AsyncMock(return_value=dummy_thread),
            ),
            patch.object(
                roll_cog, "loggable_roll", wraps=roll_cog.loggable_roll
            ) as mock_roll,
            patch.object(
                discord.Member, "create_dm", new=AsyncMock(return_value=dm_channel)
            ),
            patch(
                "NightCityBot.cogs.dm_handling.parse_dice", return_value=(1, 20, 0)
            ) as mock_parse,
        ):
            await dm_handler.dm.callback(dm_handler, ctx, user, message="!roll 1d20")
            suite.assert_send(logs, dm_channel.send, "dm.send")
        suite.assert_called(logs, mock_parse, "parse_dice")
        suite.assert_called(logs, mock_roll, "loggable_roll")
    except Exception as e:
        logs.append(f"❌ Exception in test_dm_roll_relay: {e}")
    return logs
