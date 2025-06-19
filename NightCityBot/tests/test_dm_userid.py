from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch

async def run(suite, ctx) -> List[str]:
    """Ensure !dm works with a raw user ID."""
    logs: List[str] = []
    dm = suite.bot.get_cog('DMHandler')
    member = await suite.get_test_user(ctx)
    user = getattr(member, "_user", member)
    ctx.send = AsyncMock()
    ctx.message.attachments = []
    with (
        patch.object(dm, "get_or_create_dm_thread", new=AsyncMock(return_value=MagicMock(spec=discord.Thread))),
        patch.object(type(user), "send", wraps=user.send) as send_mock,
    ):
        await dm.dm.callback(dm, ctx, user, message="Test")
        suite.assert_send(logs, send_mock, "user.send")
    return logs
