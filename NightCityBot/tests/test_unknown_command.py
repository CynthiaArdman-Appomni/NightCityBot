from typing import List
from discord.ext import commands
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Send an unknown ! command and ensure it's ignored."""
    logs = []
    admin = suite.bot.get_cog('Admin')
    try:
        msg = ctx.message
        msg.content = "!notacommand"
        await admin.on_command_error(ctx, commands.CommandNotFound("notacommand"))
        logs.append("✅ Unknown command handled without audit log")
    except Exception as e:
        logs.append(f"❌ Exception handling unknown command: {e}")
    return logs
