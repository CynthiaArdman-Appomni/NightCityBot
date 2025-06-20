from typing import List
from unittest.mock import AsyncMock, patch

async def run(suite, ctx) -> List[str]:
    """Restore the most recent balance from a user's backup log."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    member = await suite.get_test_user(ctx)
    ctx.send = AsyncMock()

    backup = [
        {"cash": 50, "bank": 20, "label": "old", "timestamp": "2025-06-01T00:00:00"},
        {"cash": 100, "bank": 50, "label": "latest", "timestamp": "2025-06-02T00:00:00"},
    ]

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("NightCityBot.cogs.economy.load_json_file", new=AsyncMock(return_value=backup)),
        patch.object(economy.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 80, "bank": 40})),
        patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)) as mock_update,
    ):
        await economy.restore_balance_command(ctx, member)
        suite.assert_called(logs, mock_update, "update_balance")

    return logs
