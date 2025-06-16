from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Test roll bonuses for Netrunner roles."""
    logs = []
    mock_author = AsyncMock(spec=discord.Member)
    mock_author.display_name = "BonusTest"
    mock_author.roles = [AsyncMock(name="Netrunner Level 2")]
    for r in mock_author.roles:
        r.name = "Netrunner Level 2"

    channel = AsyncMock(spec=discord.TextChannel)
    channel.send = AsyncMock()

    logs.append("→ Expected: Roll result should include '+1 Netrunner bonus' in output.")

    try:
        roll_system = suite.bot.get_cog('RollSystem')
        await roll_system.loggable_roll(mock_author, channel, "1d20")
        message = channel.send.call_args[0][0]
        if "+1 Netrunner bonus" in message:
            logs.append("→ Result: ✅ Found bonus text in roll output.")
        else:
            logs.append("→ Result: ❌ Bonus text missing from roll output.")
    except Exception as e:
        logs.append(f"❌ Exception in test_bonus_rolls: {e}")
    return logs
