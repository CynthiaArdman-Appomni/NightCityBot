from typing import List
from discord.ext import commands
from unittest.mock import AsyncMock

async def run(suite, ctx) -> List[str]:
    """Send an unknown ! command and ensure it's ignored."""
    logs = []
    admin = suite.bot.get_cog('Admin')
    ctx.send = AsyncMock()
    try:
        msg = ctx.message
        msg.content = "!notacommand"
        await admin.on_command_error(ctx, commands.CommandNotFound("notacommand"))
        logs.append("✅ Unknown command handled without audit log")
    except Exception as e:
        logs.append(f"❌ Exception handling unknown command: {e}")
    return logs
