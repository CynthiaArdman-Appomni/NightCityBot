from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Ensure Netrunner roles no longer grant roll bonuses."""
    logs = []
    mock_author = AsyncMock(spec=discord.Member)
    mock_author.display_name = "BonusTest"
    mock_author.roles = [AsyncMock(name="Netrunner Level 2")]
    for r in mock_author.roles:
        r.name = "Netrunner Level 2"

    channel = AsyncMock(spec=discord.TextChannel)
    channel.send = AsyncMock()

    logs.append("→ Expected: Roll result should not include 'Netrunner bonus' in output.")

    try:
        roll_system = suite.bot.get_cog('RollSystem')
        await roll_system.loggable_roll(mock_author, channel, "1d20")
        message = channel.send.call_args[0][0]
        if "Netrunner bonus" in message:
            logs.append("→ Result: ❌ Bonus text found in roll output.")
        else:
            logs.append("→ Result: ✅ No bonus text in roll output.")
    except Exception as e:
        logs.append(f"❌ Exception in test_bonus_rolls: {e}")
    return logs
