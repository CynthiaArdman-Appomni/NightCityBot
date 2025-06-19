from typing import List
from discord.ext import commands
from unittest.mock import AsyncMock

async def run(suite, ctx) -> List[str]:
    """Ensure UnbelievaBoat economy commands are ignored."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    ctx.send = AsyncMock()
    ctx.message.content = "!bal"
    try:
        await admin.on_command_error(ctx, commands.CommandNotFound('bal'))
        if ctx.send.await_count == 0:
            logs.append("✅ UnbelievaBoat command ignored")
        else:
            logs.append("❌ UnbelievaBoat command produced a message")
    except Exception as e:
        logs.append(f"❌ Exception: {e}")
    return logs
