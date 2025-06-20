from typing import List
from unittest.mock import AsyncMock

async def run(suite, ctx) -> List[str]:
    """Run the help commands."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    ctx.send = AsyncMock()
    await admin.helpme(ctx)
    await admin.helpfixer(ctx)
    if ctx.send.await_count >= 2:
        logs.append("✅ helpme and helpfixer executed")
    else:
        logs.append("❌ Help commands failed")
    return logs
