from typing import List
from unittest.mock import AsyncMock

async def run(suite, ctx) -> List[str]:
    """Ensure helpfixer splits long sections into valid chunks."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    ctx.send = AsyncMock()
    await admin.helpfixer(ctx)
    try:
        ctx.send.assert_awaited()
        for call in ctx.send.await_args_list:
            embed = call.kwargs.get('embed') or call.args[0]
            if any(len(field.value) > 1024 for field in embed.fields):
                logs.append('❌ field overflow')
                break
        else:
            logs.append('✅ chunks used')
    except Exception as e:
        logs.append(f'❌ exception {e}')
    return logs

