from typing import List
from unittest.mock import AsyncMock, patch

async def run(suite, ctx) -> List[str]:
    """Restore a balance using a label from the user's backup log."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    member = await suite.get_test_user(ctx)
    ctx.send = AsyncMock()

    backup = [
        {"cash": 50, "bank": 20, "label": "old"},
        {"cash": 100, "bank": 40, "label": "collect_rent_before"},
    ]

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("NightCityBot.cogs.economy.load_json_file", new=AsyncMock(return_value=backup)),
        patch.object(economy.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 0, "bank": 0})),
        patch.object(economy.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)) as mock_update,
    ):
        await economy.restore_balance_command(ctx, member, "collect_rent_before")
        suite.assert_called(logs, mock_update, "update_balance")

    return logs
