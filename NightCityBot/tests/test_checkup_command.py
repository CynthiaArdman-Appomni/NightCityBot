from typing import List
import discord
from unittest.mock import AsyncMock, MagicMock, patch
import config
from NightCityBot.utils.constants import ROLE_COSTS_BUSINESS, ROLE_COSTS_HOUSING

async def run(suite, ctx) -> List[str]:
    """Run the ripperdoc checkup command."""
    control = suite.bot.get_cog('SystemControl')
    if control:
        await control.set_status('cyberware', True)
    logs = []
    cyber = suite.bot.get_cog('CyberwareManager')
    if not cyber:
        logs.append("❌ CyberwareManager cog not loaded")
        return logs
    member = MagicMock(spec=discord.Member)
    member.display_name = "TestUser"
    member.roles = [discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)]
    member.remove_roles = AsyncMock()
    log_channel = MagicMock()
    log_channel.send = AsyncMock()
    with (
        patch("discord.Guild.get_role", return_value=discord.Object(id=config.CYBER_CHECKUP_ROLE_ID)),
        patch("discord.Guild.get_channel", return_value=log_channel),
        patch("NightCityBot.cogs.cyberware.save_json_file", new=AsyncMock()),
    ):
        await cyber.checkup.callback(cyber, ctx, member)
    suite.assert_send(logs, member.remove_roles, "remove_roles")
    suite.assert_send(logs, log_channel.send, "log_channel.send")
    from datetime import date
    expected = date.today().isoformat()
    if cyber.data.get(str(member.id)) == expected:
        logs.append("✅ checkup streak reset")
    else:
        logs.append("❌ checkup streak not reset")
    return logs
