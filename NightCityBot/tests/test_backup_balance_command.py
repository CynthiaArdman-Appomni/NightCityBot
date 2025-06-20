from typing import List
from unittest.mock import AsyncMock, patch

async def run(suite, ctx) -> List[str]:
    """Back up a single member's balance."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    member = await suite.get_test_user(ctx)
    ctx.send = AsyncMock()

    saved = {}

    async def fake_save(path, data):
        saved['path'] = path
        saved['data'] = data

    with (
        patch.object(economy.unbelievaboat, 'get_balance', new=AsyncMock(return_value={'cash': 100, 'bank': 50})),
        patch('NightCityBot.cogs.economy.save_json_file', new=fake_save),
        patch.object(economy, 'backup_balances', new=AsyncMock()) as mock_backup,
    ):
        await economy.backup_balance_command(ctx, member)
        suite.assert_called(logs, mock_backup, 'backup_balances')

    if saved.get('data', {}).get(str(member.id)) == {'cash': 100, 'bank': 50}:
        logs.append('✅ balance saved')
    else:
        logs.append('❌ balance not saved')

    return logs
