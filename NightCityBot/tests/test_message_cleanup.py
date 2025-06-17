from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

async def run(suite, ctx) -> List[str]:
    """Ensure !dm and !post delete the invoking message."""
    logs: List[str] = []
    dm_cog = suite.bot.get_cog('DMHandler')
    admin_cog = suite.bot.get_cog('Admin')
    user = await suite.get_test_user(ctx)

    ctx.message.delete = AsyncMock()
    ctx.message.attachments = []
    with patch.object(type(user), "send", new=AsyncMock()), \
         patch.object(dm_cog, "get_or_create_dm_thread", new=AsyncMock(return_value=MagicMock(spec=discord.Thread))):
        await dm_cog.dm.callback(dm_cog, ctx, user, message="Hello")
    if ctx.message.delete.await_count:
        logs.append("✅ !dm deleted command message")
    else:
        logs.append("❌ !dm did not delete command")

    ctx.message.delete.reset_mock()
    dest = MagicMock(spec=discord.TextChannel)
    dest.name = "general"
    dest.send = AsyncMock()
    parent = MagicMock()
    parent.threads = []
    with patch.object(type(ctx.guild), "text_channels", new=PropertyMock(return_value=[dest, parent])):
        with patch.object(suite.bot, "invoke", new=AsyncMock()):
            await admin_cog.post(ctx, dest.name, message="Test")
    if ctx.message.delete.await_count:
        logs.append("✅ !post deleted command message")
    else:
        logs.append("❌ !post did not delete command")
    return logs
