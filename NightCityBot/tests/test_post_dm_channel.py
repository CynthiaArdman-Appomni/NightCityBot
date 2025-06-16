from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Run !post from a DM thread."""
    logs: List[str] = []
    admin = suite.bot.get_cog('Admin')
    dest = MagicMock(spec=discord.TextChannel)
    dest.name = "general"
    dest.send = AsyncMock()
    thread_parent = MagicMock()
    thread_parent.threads = []
    ctx.guild.text_channels = [dest, thread_parent]
    ctx.message.attachments = []
    ctx.channel = MagicMock(spec=discord.Thread)
    ctx.send = AsyncMock()
    await admin.post(ctx, dest.name, message="Test message")
    suite.assert_send(logs, dest.send, "dest.send")
    return logs
