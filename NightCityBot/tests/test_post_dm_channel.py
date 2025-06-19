from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

async def run(suite, ctx) -> List[str]:
    """Run !post from a DM thread."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    dest = MagicMock(spec=discord.TextChannel)
    dest.name = "general"
    dest.send = AsyncMock()
    thread_parent = MagicMock()
    thread_parent.threads = []
    with patch.object(type(ctx.guild), "text_channels", new=PropertyMock(return_value=[dest, thread_parent])):
        ctx.message.attachments = []
        ctx.channel = MagicMock(spec=discord.Thread)
        ctx.send = AsyncMock()
        await admin.post(ctx, dest.name, message="Test message")
    suite.assert_send(logs, dest.send, "dest.send")
    return logs
