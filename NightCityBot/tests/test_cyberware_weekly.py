from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config

async def run(suite, ctx) -> List[str]:
    """Simulate the weekly checkup task."""
    logs: List[str] = []
    manager = suite.bot.get_cog('CyberwareManager')
    if not manager:
        logs.append("❌ CyberwareManager cog not loaded")
        return logs
    guild = MagicMock()
    check = discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)
    medium = discord.Object(id=config.CYBER_MEDIUM_ROLE_ID)
    loa = discord.Object(id=config.LOA_ROLE_ID)
    guild.get_role.side_effect = lambda rid: {config.CYBER_CHECKUP_ROLE_ID: check,
                                              config.CYBER_MEDIUM_ROLE_ID: medium, config.LOA_ROLE_ID: loa}.get(rid)
    member_a = MagicMock(spec=discord.Member)
    member_a.id = 1
    member_a.roles = [medium]
    member_a.add_roles = AsyncMock()
    member_b = MagicMock(spec=discord.Member)
    member_b.id = 2
    member_b.roles = [medium, check]
    member_b.add_roles = AsyncMock()
    guild.members = [member_a, member_b]
    log_channel = MagicMock()
    log_channel.send = AsyncMock()
    guild.get_channel.return_value = log_channel
    with (
        patch.object(suite.bot, "get_guild", return_value=guild),
        patch.object(manager.unbelievaboat, "get_balance", new=AsyncMock(return_value={"cash": 5000, "bank": 0})),
        patch.object(manager.unbelievaboat, "update_balance", new=AsyncMock(return_value=True)),
        patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
    ):
        await manager.process_week()
    suite.assert_send(logs, member_a.add_roles, "add_roles")
    suite.assert_send(logs, log_channel.send, "log_channel.send")
    return logs
