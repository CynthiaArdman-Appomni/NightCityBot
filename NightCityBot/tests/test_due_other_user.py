from typing import List
import discord
from unittest.mock import AsyncMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Ensure due can target another member."""
    logs: List[str] = []
    economy = suite.bot.get_cog('Economy')
    if not economy:
        logs.append('❌ Economy cog not loaded')
        return logs
    user = await suite.get_test_user(ctx)
    ctx.send = AsyncMock()

    captured = {}
    def fake_calculate(member):
        captured['member'] = member
        return 123, ['item']

    with patch.object(economy, 'calculate_due', side_effect=fake_calculate):
        await economy.due.callback(economy, ctx, user)

    suite.assert_send(logs, ctx.send, 'ctx.send')
    if captured.get('member') is user:
        logs.append('✅ member argument respected')
    else:
        logs.append('❌ member argument ignored')
    return logs

