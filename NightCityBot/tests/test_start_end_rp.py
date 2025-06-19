from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Create and end an RP session to confirm logging works."""
    logs = []
    rp_manager = suite.bot.get_cog('RPManager')
    channel = MagicMock(spec=discord.TextChannel)
    channel.send = AsyncMock()
    ctx.send = AsyncMock()
    # ctx.message.delete is a coroutine on real Message objects which use
    # ``__slots__``. Patch the attribute on the class to avoid ``read-only``
    # errors when running against a real Context instance.
    with patch.object(type(ctx.message), "delete", new=AsyncMock()):
        with patch.object(discord.Guild, "create_text_channel", AsyncMock(return_value=channel)) as mock_create:
            await rp_manager.start_rp(ctx, f"<@{config.TEST_USER_ID}>")
        if mock_create.await_count:
            logs.append("✅ start_rp created channel")
            ctx.channel = channel
            rp_manager.end_rp_session = AsyncMock()
            await rp_manager.end_rp(ctx)
            suite.assert_called(logs, rp_manager.end_rp_session, "end_rp_session")
        else:
            logs.append("❌ start_rp failed to create channel")
    return logs
