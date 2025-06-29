from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
import discord

async def run(suite, ctx) -> List[str]:
    """Ensure long audit messages are chunked."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    with patch.object(admin.bot, 'get_channel', return_value=channel):
        await admin.log_audit(ctx.author, 'A' * 3000)
    try:
        channel.send.assert_awaited()
        embed = channel.send.await_args.kwargs.get('embed') or channel.send.await_args.args[0]
        if len(embed.fields) > 2 and all(len(f.value) <= 1024 for f in embed.fields[1:]):
            logs.append('✅ chunks used')
        else:
            logs.append('❌ embed not chunked')
    except Exception as e:
        logs.append(f'❌ exception {e}')
    return logs
