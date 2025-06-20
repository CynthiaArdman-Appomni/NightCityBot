from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

async def run(suite, ctx) -> List[str]:
    """Test roll command in direct DMs."""
    logs = []
    try:
        user = await suite.get_test_user(ctx)
        dm_channel = MagicMock()
        with patch.object(type(user), "create_dm", new=AsyncMock(return_value=dm_channel)):
            roll_system = suite.bot.get_cog("RollSystem")
            with patch.object(roll_system, "loggable_roll", new=AsyncMock()) as mock_roll:
                await roll_system.loggable_roll(user, dm_channel, "1d6")
                suite.assert_called(logs, mock_roll, "loggable_roll")

    except Exception as e:
        logs.append(f"❌ Exception in test_roll_direct_dm: {e}")
    return logs
