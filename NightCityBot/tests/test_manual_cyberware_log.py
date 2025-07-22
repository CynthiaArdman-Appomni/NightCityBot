from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Ensure manual cyberware collection creates weekly log entry."""
    logs: List[str] = []
    cyber = suite.bot.get_cog('CyberwareManager')
    if not cyber:
        logs.append('❌ CyberwareManager cog not loaded')
        return logs
    user = await suite.get_test_user(ctx)
    # Give both author and target the approved role
    approved = discord.Object(id=config.APPROVED_ROLE_ID)
    medium = discord.Object(id=config.CYBER_MEDIUM_ROLE_ID)
    checkup = discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)
    ctx.author.roles = [approved]
    user.roles = [approved, medium, checkup]
    ctx.send = AsyncMock()
    with (
        patch('NightCityBot.cogs.cyberware.load_json_file', new=AsyncMock(return_value=[])),
        patch('NightCityBot.cogs.cyberware.save_json_file', new=AsyncMock()) as mock_save,
        patch.object(cyber.unbelievaboat, 'get_balance', new=AsyncMock(return_value={"cash": 500, "bank": 0})),
        patch.object(cyber.unbelievaboat, 'update_balance', new=AsyncMock(return_value=True)),
    ):
        await cyber.collect_cyberware.callback(cyber, ctx, user)
        suite.assert_called(logs, mock_save, 'save_json_file')
        saved = mock_save.await_args_list[-1].args[1]
        if isinstance(saved, list) and saved:
            logs.append('✅ weekly entry created')
        else:
            logs.append(f'❌ unexpected weekly data: {saved}')
    return logs
