from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch

async def run(suite, ctx) -> List[str]:
    """Run the manual balance backup command."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')

    member = await suite.get_test_user(ctx)
    guild = MagicMock()
    guild.members = [member]
    ctx.guild = guild
    ctx.send = AsyncMock()

    saved = {}

    async def fake_save(path, data):
        saved['path'] = path
        saved['data'] = data

    with (
        patch.object(economy.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 100, "bank": 50})),
        patch("NightCityBot.cogs.economy.save_json_file", new=fake_save),
        patch.object(economy, "backup_balances", new=AsyncMock()) as mock_backup,
    ):
        await economy.backup_balances_command(ctx)
        suite.assert_called(logs, mock_backup, "backup_balances")

    if saved.get("data", {}).get(str(member.id)) == {"cash": 100, "bank": 50}:
        logs.append("✅ balances saved")
    else:
        logs.append("❌ balances not saved")

    return logs
